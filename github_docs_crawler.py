import os
import json
import time
import requests
from urllib.parse import urlparse
from datetime import datetime

# == CONFIGURATION SETTINGS ==
DEFAULT_CHUNK_SIZE = 50            # Number of files per JSON chunk
DEFAULT_MAX_DEPTH = 10             # Maximum directory recursion depth
DEFAULT_FILE_EXTENSIONS = [        # File types to crawl
    '.md', '.html', '.txt', 
    '.rst', '.adoc', '.markdown'
]
OUTPUT_BASE_DIR = "github_api_crawled_data"  # Base output directory
REQUEST_DELAY = 0.5                # Seconds between API requests
RATE_LIMIT_BUFFER = 10             # Minimum remaining requests before pausing
# ============================

class GitHubAPICrawler:
    def __init__(self, repo_url, token=None, **kwargs):
        # Parse configuration from arguments and defaults
        self.config = {
            'chunk_size': kwargs.get('chunk_size', DEFAULT_CHUNK_SIZE),
            'max_depth': kwargs.get('max_depth', DEFAULT_MAX_DEPTH),
            'extensions': kwargs.get('extensions', DEFAULT_FILE_EXTENSIONS),
            'request_delay': kwargs.get('request_delay', REQUEST_DELAY),
        }
        
        # Extract repository information
        self.parse_repo_url(repo_url)
        self.token = token or os.getenv('GITHUB_TOKEN')
        
        # Configure API connection
        self.session = requests.Session()
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}
        self.base_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents"
        
        # Initialize crawling state
        self.crawled_data = []
        self.chunk_counter = 1
        self.rate_limit_remaining = 5000  # Default for authenticated requests
        
        # Set up output directory structure
        self.output_dir = os.path.join(
            OUTPUT_BASE_DIR,
            f"{self.owner}-{self.repo}"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_repo_url(self, url):
        """Extract owner, repo, and base path from GitHub URL"""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        self.owner = path_parts[0]
        self.repo = path_parts[1]
        
        # Handle tree paths
        if len(path_parts) > 3 and path_parts[2] == 'tree':
            self.base_path = '/'.join(path_parts[4:])
        else:
            self.base_path = ''

    def check_rate_limit(self):
        """Monitor and enforce GitHub API rate limits"""
        if self.rate_limit_remaining <= RATE_LIMIT_BUFFER:
            reset_time = int(self.session.get(
                'https://api.github.com/rate_limit'
            ).json()['resources']['core']['reset'])
            
            sleep_time = max(reset_time - int(time.time()), 0) + 10
            print(f"Rate limit low. Pausing for {sleep_time} seconds")
            time.sleep(sleep_time)
            self.rate_limit_remaining = 5000  # Reset after sleep

    def get_api_content(self, path):
        """Fetch content from GitHub API with error handling"""
        self.check_rate_limit()
        url = f"{self.base_api_url}/{path}"
        
        try:
            response = self.session.get(url, headers=self.headers)
            self.rate_limit_remaining = int(
                response.headers.get('X-RateLimit-Remaining', 10)
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print("Rate limit exceeded, waiting...")
                time.sleep(60)
                return self.get_api_content(path)
                
        except Exception as e:
            print(f"API request failed: {str(e)}")
            return None
        
        return None

    def process_content(self, content, current_depth):
        """Recursive content processing with depth control"""
        if current_depth > self.config['max_depth']:
            return

        if isinstance(content, list):
            for item in content:
                self.process_item(item, current_depth)
        elif isinstance(content, dict):
            self.process_item(content, current_depth)

    def process_item(self, item, current_depth):
        """Handle individual files and directories"""
        if item['type'] == 'dir':
            self.process_directory(item['path'], current_depth + 1)
        elif item['type'] == 'file':
            self.process_file(item)

    def process_directory(self, path, current_depth):
        """Process directory contents"""
        print(f"Processing directory: {path}")
        content = self.get_api_content(path)
        time.sleep(self.config['request_delay'])
        
        if content:
            self.process_content(content, current_depth)

    def process_file(self, item):
        """Download and store file contents"""
        if any(item['name'].lower().endswith(ext) 
             for ext in self.config['extensions']):
            
            print(f"Downloading: {item['path']}")
            content = self.download_content(item['download_url'])
            
            if content:
                self.store_document(item, content)

    def download_content(self, download_url):
        """Download file contents with error handling"""
        try:
            response = self.session.get(download_url, headers=self.headers)
            time.sleep(self.config['request_delay'])
            return response.text
        except Exception as e:
            print(f"Download failed: {str(e)}")
            return None

    def store_document(self, item, content):
        """Store document data in memory chunk"""
        self.crawled_data.append({
            'path': item['path'],
            'url': item['html_url'],
            'content': content,
            'sha': item['sha'],
            'size': item['size'],
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.crawled_data) >= self.config['chunk_size']:
            self.save_chunk()

    def save_chunk(self):
        """Save current chunk to organized directory structure"""
        if not self.crawled_data:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"chunk_{timestamp}_{self.chunk_counter}.json"
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'repo': f"{self.owner}/{self.repo}",
                    'base_path': self.base_path,
                    'crawled_at': datetime.now().isoformat()
                },
                'documents': self.crawled_data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Saved chunk {self.chunk_counter} with {len(self.crawled_data)} documents")
        self.crawled_data = []
        self.chunk_counter += 1

    def crawl(self):
        """Main crawl execution method"""
        print(f"\nStarting crawl of {self.owner}/{self.repo}")
        print(f"Output directory: {os.path.abspath(self.output_dir)}")
        
        start_path = self.base_path or ''
        self.process_directory(start_path, 0)
        self.save_chunk()  # Save remaining documents
        
        print(f"\nCrawl complete. Total documents processed: "
              f"{(self.chunk_counter-1)*self.config['chunk_size'] + len(self.crawled_data)}")

def main():
    print("GitHub API Documentation Crawler")
    print("--------------------------------")
    
    repo_url = input("Enter GitHub repository URL: ").strip()
    token = input("GitHub token (optional, press enter to skip): ").strip()
    
    crawler = GitHubAPICrawler(
        repo_url=repo_url,
        token=token if token else None,
        chunk_size=DEFAULT_CHUNK_SIZE,
        max_depth=DEFAULT_MAX_DEPTH,
        extensions=DEFAULT_FILE_EXTENSIONS,
        request_delay=REQUEST_DELAY
    )
    
    crawler.crawl()

if __name__ == "__main__":
    main()
