import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import time
import os

# Exclude URLs with hashtags, question marks, and equals signs
exclude = [
        # Language specific pages
        'lang=go', 'lang=node', 'lang=rest', 'lang=ruby', 
        'lang=java', 'lang=javascript', 'lang=php', 'lang=typescript',
        
        # User interface elements
        '#', # '?', '=',
        
        # Authentication and user pages
        '/login', '/signin', '/signup', '/register',
        '/logout', '/signout', '/auth/',
        '/password', '/reset', '/forgot',
        
        # Account and settings pages
        '/settings', '/profile', '/account', '/preferences',
        '/dashboard', '/admin', '/user/',
        
        # Common utility pages
        '/search', '/filter', '/sort',
        '/print', '/download', '/upload',
        '/raw/', '/blame/', '/commits/',
        
        # Social and interaction pages
        '/comment', '/like', '/share', '/follow',
        
        # Common API and technical paths
        '/graphql', '/webhook',
        '/feeds/', '/rss/', '/atom/',
        
        # Session and tracking related
        '/session', '/track', '/analytics',
        
        # Common GitHub-specific paths (if crawling GitHub)
        '/pulse/', '/network/', '/graphs/',
        '/issues/new', '/pull/', '/compare/',
        '/edit/', '/delete/', '/archive/',
        '/stargazers', '/subscribers', '/fork'
    ]
    
class WebCrawler:

    
    def __init__(self, base_url, chunk_size=50):
        self.base_url = base_url
        parsed_url = urlparse(base_url)
        self.domain = parsed_url.netloc
        self.base_path = parsed_url.path.rstrip('/')
        self.visited_urls = set()
        self.chunk_size = chunk_size
        self.current_chunk = []
        self.chunk_counter = 1
        self.total_pages = 0
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def save_chunk(self, timestamp):
        """Save current chunk to a JSON file"""
        if not self.current_chunk:
            return

        # Create directory if it doesn't exist
        os.makedirs('crawled_data', exist_ok=True)
        
        filename = f"crawled_data/crawled_data_{timestamp}_chunk{self.chunk_counter}.json"
        
        output = {
            'base_url': self.base_url,
            'base_path': self.base_path,
            'crawl_date': datetime.now().isoformat(),
            'chunk_number': self.chunk_counter,
            'pages': self.current_chunk
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        
        print(f"Saved chunk {self.chunk_counter} to {filename}")
        self.current_chunk = []  # Clear the chunk
        self.chunk_counter += 1

    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and is under the specified path"""
        parsed_url = urlparse(url)
        if any(pattern in url.lower() for pattern in exclude):
            return False
        # Check if the URL is in the same domain and starts with the base path
        return (self.domain in parsed_url.netloc and 
                parsed_url.path.startswith(self.base_path))
    
    def get_page_content(self, url):
        """Fetch and parse page content"""
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            page_data = {
                'url': url,
                'title': soup.title.string if soup.title else 'No title',
                'text_content': soup.get_text(separator=' ', strip=True),
                'meta_description': '',
                'links': [],
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code
            }
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                page_data['meta_description'] = meta_desc.get('content', '')
            
            return page_data, soup
            
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None, None

    def extract_links(self, soup, current_url):
        """Extract all links from the page"""
        links = []
        if soup:
            for link in soup.find_all('a', href=True):
                url = link['href']
                absolute_url = urljoin(current_url, url)
                if self.is_valid_url(absolute_url):
                    links.append(absolute_url)
        return links

    def crawl(self, max_pages=None):
        """Main crawling function with chunking support"""
        urls_to_visit = [self.base_url]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        while urls_to_visit and (max_pages is None or self.total_pages < max_pages):
            current_url = urls_to_visit.pop(0)
            
            if current_url not in self.visited_urls:
                print(f"Crawling: {current_url}")
                self.visited_urls.add(current_url)
                
                page_data, soup = self.get_page_content(current_url)
                
                if page_data:
                    links = self.extract_links(soup, current_url)
                    page_data['links'] = links
                    self.current_chunk.append(page_data)
                    self.total_pages += 1
                    
                    # Save chunk when it reaches the chunk size
                    if len(self.current_chunk) >= self.chunk_size:
                        self.save_chunk(timestamp)
                    
                    urls_to_visit.extend([url for url in links if url not in self.visited_urls])
        
        # Save any remaining pages in the last chunk
        if self.current_chunk:
            self.save_chunk(timestamp)
        
        print(f"\nCrawl completed! Total pages crawled: {self.total_pages}")
        print(f"Data saved in {self.chunk_counter - 1} chunks")

def main():
    print("Website Crawler")
    print("-" * 50)
    
    url = input("Enter the website URL to crawl (e.g., https://example.com/path): ").strip()
    chunk_size = input("Enter chunk size (default is 50): ").strip()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        chunk_size = int(chunk_size) if chunk_size else 50
        crawler = WebCrawler(url, chunk_size=chunk_size)
        print(f"\nStarting crawl of {url}")
        print("This may take a while depending on the website size...")
        crawler.crawl()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()