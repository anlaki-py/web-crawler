import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import re
import urllib.robotparser

# Exclude URLs with hashtags, question marks, and equals signs
exclude = [
    'lang=go', 'lang=node', 'lang=rest', 'lang=ruby',
    'lang=java', 'lang=javascript', 'lang=php', 'lang=typescript',
    '/france', '#', 
    '/login', '/signin', '/signup', '/register',
    '/logout', '/signout', '/auth/',
    '/password', '/reset', '/forgot',
    '/settings', '/profile', '/account', '/preferences',
    '/dashboard', '/admin', '/user/',
    '/search', '/filter', '/sort',
    '/print', '/download', '/upload',
    '/raw/', '/blame/', '/commits/',
    '/comment', '/like', '/share', '/follow',
    '/graphql', '/webhook',
    '/feeds/', '/rss/', '/atom/',
    '/session', '/track', '/analytics',
    '.zip', '.pdf', '/assets/', 
    '.png', '.webp', '.jpg', '.jpeg'
]

class WebCrawler:
    
    def __init__(self, base_url, chunk_size=50, max_depth=3):
        self.base_url = base_url
        self.max_depth = max_depth
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
        
        # Initialize robots.txt parser
        self.robot_parser = urllib.robotparser.RobotFileParser()
        robots_url = urljoin(base_url, "/robots.txt")
        self.robot_parser.set_url(robots_url)
        self.robot_parser.read()

    def save_chunk(self, timestamp):
        """Save current chunk to a JSON file"""
        if not self.current_chunk:
            return

        os.makedirs('crawled_data', exist_ok=True)
        
        filename = f"crawled_data/crawled_data_{timestamp}_chunk{self.chunk_counter}.json"
        
        output = {
            'base_url': self.base_url,
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
                parsed_url.path.startswith(self.base_path) and 
                self.robot_parser.can_fetch('*', url))

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

    def crawl_page(self, current_url, depth):
        """Crawl a single page and extract links"""
        if depth > self.max_depth or current_url in self.visited_urls:
            return
        
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
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                self.save_chunk(timestamp)

            # Crawl extracted links recursively up to max depth
            for link in links:
                self.crawl_page(link, depth + 1)

    def crawl(self):
        """Main crawling function"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Start crawling from the base URL at depth 0
        self.crawl_page(self.base_url, 0)

        # Save any remaining pages in the last chunk
        if self.current_chunk:
            self.save_chunk(timestamp)

        print(f"\nCrawl completed! Total pages crawled: {self.total_pages}")
        

def main():
    print("Website Crawler")
    print("-" * 50)
    
    url = input("Enter the website URL to crawl (e.g., https://example.com/path): ").strip()
    
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        chunk_size = int(input("Enter chunk size (default is 50): ").strip() or 50)
        
        max_depth = int(input("Enter maximum crawl depth (default is 3): ").strip() or 3)
        
        crawler = WebCrawler(url, chunk_size=chunk_size, max_depth=max_depth)
        
        print(f"\nStarting crawl of {url}")
        
        crawler.crawl()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
    