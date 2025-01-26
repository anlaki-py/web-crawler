import os
import json
import re
import threading
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
from queue import Queue
from collections import defaultdict
from requests.exceptions import RequestException

# Constants for file paths
CRAWL_OUTPUT_DIR = 'crawled_data'
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Exclusion patterns
EXCLUDE_PATTERNS = [
    'lang=', '#', '/login', '/signin', '/signup', '/register', '/logout', 
    '/settings', '/profile', '/account', '/search', '/filter', '/upload', 
    '.zip', '.pdf', '.png', '.jpg', '.jpeg', '.webp'
]

class WebCrawler:
    def __init__(self, base_url, chunk_size=50, max_depth=3, threads=5):
        self.base_url = base_url
        parsed_url = urlparse(base_url)
        self.domain = parsed_url.netloc
        self.base_path = parsed_url.path.rstrip('/')
        self.visited_urls = set()
        self.queue = Queue()
        self.queue.put((base_url, 0))  # Add URL with depth
        self.chunk_size = chunk_size
        self.max_depth = max_depth
        self.threads = threads
        self.current_chunk = []
        self.chunk_counter = 1
        self.total_pages = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': DEFAULT_USER_AGENT})

        os.makedirs(CRAWL_OUTPUT_DIR, exist_ok=True)

    def save_chunk(self, timestamp):
        """Save current chunk to a JSON file."""
        if not self.current_chunk:
            return

        filename = os.path.join(CRAWL_OUTPUT_DIR, f'crawled_data_{timestamp}_chunk{self.chunk_counter}.json')
        output = {
            'base_url': self.base_url,
            'crawl_date': datetime.now().isoformat(),
            'chunk_number': self.chunk_counter,
            'pages': self.current_chunk
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print(f"Saved chunk {self.chunk_counter} to {filename}")
        self.current_chunk = []  # Reset the chunk
        self.chunk_counter += 1

    def is_valid_url(self, url):
        """Validate URL based on domain, path, and exclusion patterns."""
        parsed_url = urlparse(url)
        if parsed_url.netloc != self.domain or any(pattern in url for pattern in EXCLUDE_PATTERNS):
            return False
        return True

    def fetch_content(self, url):
        """Fetch page content and return parsed data."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            page_data = {
                'url': url,
                'title': soup.title.string if soup.title else 'No title',
                'meta_description': soup.find('meta', attrs={'name': 'description'}).get('content', '') if soup.find('meta', attrs={'name': 'description'}) else '',
                'text_content': soup.get_text(separator=' ', strip=True),
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'links': []
            }

            return page_data, soup
        except RequestException as e:
            print(f"Failed to fetch {url}: {str(e)}")
            return None, None

    def extract_links(self, soup, current_url):
        """Extract valid links from a BeautifulSoup object."""
        links = []
        if soup:
            for tag in soup.find_all('a', href=True):
                absolute_url = urljoin(current_url, tag['href'])
                if self.is_valid_url(absolute_url):
                    links.append(absolute_url)
        return links

    def crawl_url(self, url, depth):
        """Crawl a single URL."""
        if url in self.visited_urls or depth > self.max_depth:
            return

        self.visited_urls.add(url)
        print(f"Crawling: {url} at depth {depth}")
        page_data, soup = self.fetch_content(url)
        if page_data:
            links = self.extract_links(soup, url)
            page_data['links'] = links
            self.current_chunk.append(page_data)
            self.total_pages += 1

            # Add new links to the queue
            for link in links:
                if link not in self.visited_urls:
                    self.queue.put((link, depth + 1))

            # Save chunk if it reaches the chunk size
            if len(self.current_chunk) >= self.chunk_size:
                self.save_chunk(datetime.now().strftime('%Y%m%d_%H%M%S'))

    def crawl(self):
        """Main crawling function using multithreading."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            while not self.queue.empty():
                url, depth = self.queue.get()
                executor.submit(self.crawl_url, url, depth)

        # Save remaining pages in the last chunk
        if self.current_chunk:
            self.save_chunk(timestamp)

        print(f"\nCrawl completed! Total pages crawled: {self.total_pages}")

def main():
    print("Enhanced Web Crawler")
    print("-" * 50)
    url = input("Enter the website URL to crawl (e.g., https://example.com): ").strip()
    chunk_size = input("Enter chunk size (default is 50): ").strip()
    max_depth = input("Enter maximum crawl depth (default is 3): ").strip()
    threads = input("Enter number of threads (default is 5): ").strip()

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        chunk_size = int(chunk_size) if chunk_size else 50
        max_depth = int(max_depth) if max_depth else 3
        threads = int(threads) if threads else 5
        crawler = WebCrawler(url, chunk_size=chunk_size, max_depth=max_depth, threads=threads)
        print(f"\nStarting crawl of {url} with chunk size {chunk_size}, max depth {max_depth}, and {threads} threads...")
        crawler.crawl()
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()