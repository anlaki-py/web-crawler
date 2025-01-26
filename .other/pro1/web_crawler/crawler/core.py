import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import is_valid_url, resolve_url, sanitize_filename
from .robots import RobotsParser
from .data_extraction import extract_data, extract_json_data
from .reporting import Reporting
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self, config):
        self.config = config
        self.base_urls = config['urls']['start_urls']
        self.max_depth = config['crawl']['max_depth']
        self.max_pages = config['crawl']['max_pages']
        self.concurrency = config['crawl']['concurrency']
        self.chunk_size = config['crawl']['chunk_size']
        self.retry_attempts = config['crawl']['retry_attempts']
        self.retry_delay = config['crawl']['retry_delay']
        self.respect_robots = config['crawl']['respect_robots']
        self.timeout = config['crawl']['timeout']
        self.user_agent = config['crawl']['user_agent']
        self.include_patterns = config['urls']['include_patterns']
        self.exclude_patterns = config['urls']['exclude_patterns']
        self.exclude_exact = config['urls']['exclude_exact']
        self.output_directory = config['output']['directory']
        self.report_format = config['output']['report_format']
        self.auth_type = config['authentication']['type']
        self.auth_username = config['authentication']['username']
        self.auth_password = config['authentication']['password']
        self.extraction_rules = config['extraction'].get('rules', {})

        self.visited_urls = set()
        self.current_chunk = []
        self.chunk_counter = 1
        self.total_pages = 0
        self.robots_parsers = {}
        self.reporting = Reporting(self.output_directory, self.report_format)

        self.session = requests.Session()
        if self.auth_type == 'basic':
            self.session.auth = (self.auth_username, self.auth_password)
        self.session.headers.update({'User-Agent': self.user_agent})

    async def fetch_page_content_async(self, session, url):
        try:
            async with session.get(url, timeout=self.timeout) as response:
                response.raise_for_status()
                html_content = await response.text()
                return html_content, response.status
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.reporting.register_error(url, e)
            logger.error(f"Error fetching {url}: {e}")
            return None, None

    def fetch_page_content(self, url):
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content, response.status_code
        except requests.exceptions.RequestException as e:
            self.reporting.register_error(url, e)
            logger.error(f"Error fetching {url}: {e}")
            return None, None

    async def process_page_async(self, session, url, depth):
        if self.max_pages is not None and self.total_pages >= self.max_pages:
            return []
        if depth > self.max_depth or url in self.visited_urls:
            return []

        self.visited_urls.add(url)
        logger.info(f"Crawling (Async): {url}")

        html_content, status_code = await self.fetch_page_content_async(session, url)
        if html_content is None:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = soup.title.string if soup.title else 'No title'
        page_text = soup.get_text(separator=' ', strip=True)
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_description.get('content', '') if meta_description else ''

        extracted_data = extract_data(soup, self.extraction_rules)
        extracted_json_data = extract_json_data(html_content)

        page_data = {
                'base_url': str(self.base_urls),
                'url': url,
                'title': page_title,
                'text_content': page_text,
                'meta_description': meta_description,
                'links': [],
                'depth' : depth,
                'timestamp': datetime.now().isoformat(),
                'status_code': status_code,
                'extracted_data': extracted_data,
                'json_ld_data': extracted_json_data
            }
        self.reporting.register_page_crawled(url)
        self.total_pages += 1
        self.current_chunk.append(page_data)
        if len(self.current_chunk) >= self.chunk_size:
            self.reporting.save_chunk(self.current_chunk, self.chunk_counter)
            self.current_chunk = []
            self.chunk_counter += 1
        links = self.extract_links(soup, url)
        page_data['links'] = links
        tasks = []
        for link in links:
            if self.max_pages is not None and self.total_pages >= self.max_pages:
                break
            tasks.append(self.process_page_async(session, link, depth + 1))
        results = await asyncio.gather(*tasks)
        all_links = links
        for result in results:
            all_links.extend(result)
        return all_links

    def extract_links(self, soup, current_url):
        links = []
        if soup:
            for link in soup.find_all('a', href=True):
                url = link['href']
                absolute_url = resolve_url(current_url, url)
                parsed_url = urlparse(absolute_url)
                base_domain = parsed_url.netloc
                base_path = parsed_url.path.rsplit('/', 1)[0] if '/' in parsed_url.path else parsed_url.path
                if is_valid_url(absolute_url, base_domain, base_path, self.include_patterns, self.exclude_patterns, self.exclude_exact) and absolute_url not in self.visited_urls:
                    if self.respect_robots:
                        if base_domain not in self.robots_parsers:
                            self.robots_parsers[base_domain] = RobotsParser(f"{parsed_url.scheme}://{base_domain}")
                        if not self.robots_parsers[base_domain].is_allowed(absolute_url):
                            continue
                        delay = self.robots_parsers[base_domain].get_crawl_delay()
                        if delay:
                            time.sleep(delay)
                    links.append(absolute_url)
        return links

    async def crawl_async(self):
        if not self.base_urls:
            logger.error("No starting URLs provided.")
            return
        async with aiohttp.ClientSession(headers={'User-Agent': self.user_agent}) as session:
            tasks = [self.process_page_async(session, url, 1) for url in self.base_urls if is_valid_url(url, urlparse(url).netloc, urlparse(url).path, self.include_patterns, self.exclude_patterns, self.exclude_exact)]
            await asyncio.gather(*tasks)

        if self.current_chunk:
            self.reporting.save_chunk(self.current_chunk, self.chunk_counter)

        self.reporting.generate_report()
        print(f"\nCrawl completed! Total pages crawled: {self.total_pages}")
        print(f"Data saved in {self.reporting.chunk_counter} chunks")

    def crawl(self):
        if not self.base_urls:
            logger.error("No starting URLs provided.")
            return
        start_time = time.time()
        urls_to_visit = list(self.base_urls)
        for url in self.base_urls:
            parsed_url = urlparse(url)
            if not is_valid_url(url, parsed_url.netloc, parsed_url.path, self.include_patterns, self.exclude_patterns, self.exclude_exact):
                logger.warning(f"Invalid starting URL: {url}. Skipping.")
                continue  # Skip invalid starting URLs
            if self.max_pages is not None and self.total_pages >= self.max_pages:
                break
            try:
                asyncio.run(self.crawl_async())
            except Exception as e:
                logger.exception(f"An unexpected error occurred during crawling: {e}")
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Crawling finished in {elapsed_time:.2f} seconds.")
        
        