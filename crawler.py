import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import time
import logging
import asyncio
import aiohttp
from typing import Set, List, Dict, Optional
import robots_parser
from collections import deque
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import re
from dataclasses import dataclass, asdict
import random

@dataclass
class PageData:
    url: str
    title: str
    text_content: str
    meta_description: str
    links: List[str]
    timestamp: str
    status_code: int
    headers: Dict
    content_type: str
    content_hash: str
    depth: int
    keywords: List[str]
    images: List[str]

class DatabaseManager:
    def __init__(self, db_name: str = "crawler.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    content_hash TEXT,
                    last_crawled TEXT,
                    data JSON
                )
            """)

    def save_page(self, page_data: PageData):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO pages (url, content_hash, last_crawled, data) VALUES (?, ?, ?, ?)",
                (page_data.url, page_data.content_hash, page_data.timestamp, json.dumps(asdict(page_data)))
            )

    def get_page(self, url: str) -> Optional[Dict]:
        cursor = self.conn.execute("SELECT data FROM pages WHERE url = ?", (url,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.delay = 1.0 / requests_per_second
        self.last_request = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_request
            if time_passed < self.delay:
                await asyncio.sleep(self.delay - time_passed)
            self.last_request = time.time()

class ModernWebCrawler:
    def __init__(self, 
                 base_url: str,
                 max_depth: int = 3,
                 max_pages: int = 100,
                 concurrent_requests: int = 10,
                 requests_per_second: float = 2.0,
                 respect_robots: bool = True,
                 user_agent: str = "ModernWebCrawler/1.0"):
        
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.concurrent_requests = concurrent_requests
        self.user_agent = user_agent
        
        # Initialize components
        self.visited_urls: Set[str] = set()
        self.url_queue = deque()
        self.db = DatabaseManager()
        self.rate_limiter = RateLimiter(requests_per_second)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='crawler.log'
        )
        self.logger = logging.getLogger(__name__)

        # Robots.txt handling
        if respect_robots:
            self.robots = robots_parser.RobotsParser(f"{self.base_url}/robots.txt")
        else:
            self.robots = None

    async def initialize(self):
        """Initialize async session and other resources"""
        self.session = aiohttp.ClientSession(headers={
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        })

    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    def is_valid_url(self, url: str) -> bool:
        """Enhanced URL validation"""
        try:
            parsed = urlparse(url)
            if not parsed.netloc or not parsed.scheme:
                return False
            if self.domain not in parsed.netloc:
                return False
            if self.robots and not self.robots.can_fetch(self.user_agent, url):
                return False
            # Ignore common non-content URLs
            ignored_patterns = [
                r'\.(jpg|jpeg|gif|png|css|js|xml|pdf)$',
                r'(calendar|login|logout|signup|admin)',
                r'#.*$'
            ]
            return not any(re.search(pattern, url, re.I) for pattern in ignored_patterns)
        except Exception:
            return False

    def compute_content_hash(self, content: str) -> str:
        """Compute MD5 hash of content to detect duplicates"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    async def get_page_content(self, url: str, depth: int) -> Optional[PageData]:
        """Fetch and parse page content with improved error handling"""
        try:
            await self.rate_limiter.acquire()
            
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None

                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type.lower():
                    return None

                text = await response.text()
                soup = BeautifulSoup(text, 'lxml')

                # Extract content
                content = self.extract_content(soup)
                content_hash = self.compute_content_hash(content)

                # Check for duplicate content
                if self.is_duplicate_content(content_hash):
                    return None

                # Extract metadata
                keywords = self.extract_keywords(soup)
                images = self.extract_images(soup, url)

                page_data = PageData(
                    url=url,
                    title=soup.title.string if soup.title else '',
                    text_content=content,
                    meta_description=self.extract_meta_description(soup),
                    links=self.extract_links(soup, url),
                    timestamp=datetime.now().isoformat(),
                    status_code=response.status,
                    headers=dict(response.headers),
                    content_type=content_type,
                    content_hash=content_hash,
                    depth=depth,
                    keywords=keywords,
                    images=images
                )

                return page_data

        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def extract_content(self, soup: BeautifulSoup) -> str:
        """Extract meaningful content while removing boilerplate"""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        return soup.get_text(separator=' ', strip=True)

    def extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags and content"""
        keywords = set()
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords.update(k.strip().lower() for k in meta_keywords.get('content', '').split(','))

        # Extract from headings
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            keywords.update(heading.get_text().lower().split())

        return list(keywords)

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from the page"""
        images = []
        for img in soup.find_all('img', src=True):
            img_url = urljoin(base_url, img['src'])
            if img_url.startswith(('http://', 'https://')):
                images.append(img_url)
        return images

    def is_duplicate_content(self, content_hash: str) -> bool:
        """Check if content has been seen before"""
        cursor = self.db.conn.execute("SELECT 1 FROM pages WHERE content_hash = ?", (content_hash,))
        return cursor.fetchone() is not None

    async def crawl(self):
        """Main crawling function with async implementation"""
        await self.initialize()
        self.url_queue.append((self.base_url, 0))

        try:
            tasks = []
            while self.url_queue and len(self.visited_urls) < self.max_pages:
                while len(tasks) < self.concurrent_requests and self.url_queue:
                    url, depth = self.url_queue.popleft()
                    if url not in self.visited_urls and depth <= self.max_depth:
                        tasks.append(asyncio.create_task(self.process_url(url, depth)))

                if tasks:
                    await asyncio.gather(*tasks)
                    tasks.clear()

        finally:
            await self.close()

    async def process_url(self, url: str, depth: int):
        """Process a single URL"""
        self.visited_urls.add(url)
        self.logger.info(f"Crawling: {url} (depth: {depth})")

        page_data = await self.get_page_content(url, depth)
        if page_data:
            self.db.save_page(page_data)
            
            # Add new URLs to queue
            for link in page_data.links:
                if link not in self.visited_urls:
                    self.url_queue.append((link, depth + 1))

    def save_to_json(self, filename: str = "crawled_data.json"):
        """Export crawled data to JSON"""
        cursor = self.db.conn.execute("SELECT data FROM pages")
        pages_data = [json.loads(row[0]) for row in cursor.fetchall()]
        
        output = {
            'base_url': self.base_url,
            'crawl_date': datetime.now().isoformat(),
            'total_pages': len(pages_data),
            'pages': pages_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

async def main():
    print("Advanced Website Crawler")
    print("-" * 50)
    
    url = input("Enter the website URL to crawl: ").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        crawler = ModernWebCrawler(
            base_url=url,
            max_depth=3,
            max_pages=100,
            concurrent_requests=10,
            requests_per_second=2.0
        )
        
        print(f"\nStarting crawl of {url}")
        await crawler.crawl()
        crawler.save_to_json()
        print("\nCrawl completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
    