import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import time

class WebCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        parsed_url = urlparse(base_url)
        self.domain = parsed_url.netloc
        self.base_path = parsed_url.path.rstrip('/')  # Store the base path
        self.visited_urls = set()
        self.pages_data = []
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and is under the specified path"""
        parsed_url = urlparse(url)
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
        """Main crawling function with optional page limit"""
        urls_to_visit = [self.base_url]
        
        while urls_to_visit and (max_pages is None or len(self.pages_data) < max_pages):
            current_url = urls_to_visit.pop(0)
            
            if current_url not in self.visited_urls:
                print(f"Crawling: {current_url}")
                self.visited_urls.add(current_url)
                
                page_data, soup = self.get_page_content(current_url)
                
                if page_data:
                    links = self.extract_links(soup, current_url)
                    page_data['links'] = links
                    self.pages_data.append(page_data)
                    
                    urls_to_visit.extend([url for url in links if url not in self.visited_urls])

    def save_to_json(self, filename="crawled_data/crawled_data.json"):
        """Save the crawled data to a JSON file"""
        output = {
            'base_url': self.base_url,
            'base_path': self.base_path,
            'crawl_date': datetime.now().isoformat(),
            'total_pages': len(self.pages_data),
            'pages': self.pages_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        
        print(f"\nCrawl completed! Data saved to {filename}")
        print(f"Total pages crawled: {len(self.pages_data)}")

def main():
    print("Website Crawler")
    print("-" * 50)
    
    url = input("Enter the website URL to crawl (e.g., https://example.com/path): ").strip()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        crawler = WebCrawler(url)
        print(f"\nStarting crawl of {url}")
        print("This may take a while depending on the website size...")
        crawler.crawl()
        crawler.save_to_json()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()