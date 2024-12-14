import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AsyncWebCrawler:
    def __init__(self, base_url, max_concurrent=20):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.pages_data = []
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)  # Limit concurrent requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_valid_url(self, url):
        """Check if URL belongs to the same domain"""
        return self.domain in url

    async def get_page_content(self, url):
        """Fetch and parse page content asynchronously"""
        try:
            async with self.semaphore:
                async with self.session.get(url, headers=self.headers, timeout=10) as response:  # Added timeout
                    response.raise_for_status()
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')

                    page_data = {
                        'url': url,
                        'title': soup.title.string if soup.title else 'No title',
                        'text_content': soup.get_text(separator=' ', strip=True),
                        'meta_description': '',
                        'links': [],
                        'timestamp': datetime.now().isoformat(),
                        'status_code': response.status
                    }

                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        page_data['meta_description'] = meta_desc.get('content', '')

                    return page_data, soup
        except aiohttp.ClientError as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return None, None
        except asyncio.TimeoutError:
            logging.error(f"Timeout fetching {url}")
            return None, None
        except Exception as e:
            logging.error(f"Unexpected error fetching {url}: {str(e)}")
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

    async def crawl_page(self, url):
        """Crawl a single page"""
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        logging.info(f"Crawling: {url}")

        page_data, soup = await self.get_page_content(url)

        if page_data:
            links = self.extract_links(soup, url)
            page_data['links'] = links
            self.pages_data.append(page_data)

            return links

        return []

    async def crawl(self):
        """Main crawling function"""
        urls_to_visit = [self.base_url]

        async with aiohttp.ClientSession() as session:
            self.session = session

            while urls_to_visit:
                tasks = [self.crawl_page(url) for url in urls_to_visit]
                results = await asyncio.gather(*tasks)

                urls_to_visit = []
                for links in results:
                    if links:
                        for link in links:
                             if link not in self.visited_urls:
                                urls_to_visit.append(link)

    def save_to_json(self, filename="crawled_data.json"):
        """Save the crawled data to a JSON file"""
        output = {
            'base_url': self.base_url,
            'crawl_date': datetime.now().isoformat(),
            'total_pages': len(self.pages_data),
            'pages': self.pages_data
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print(f"\nCrawl completed! Data saved to {filename}")
        print(f"Total pages crawled: {len(self.pages_data)}")

async def main():
    print("Website Crawler")
    print("-" * 50)

    url = input("Enter the website URL to crawl (e.g., https://example.com): ").strip()

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        crawler = AsyncWebCrawler(url)
        print(f"\nStarting crawl of {url}")
        print("This may take a while depending on the website size...")
        await crawler.crawl()
        crawler.save_to_json()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

