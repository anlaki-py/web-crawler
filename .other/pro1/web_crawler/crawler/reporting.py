import json
import os
from datetime import datetime
from .utils import sanitize_filename

class Reporting:
    def __init__(self, output_directory, report_format='text'):
        self.output_directory = output_directory
        self.report_format = report_format
        os.makedirs(self.output_directory, exist_ok=True)
        self.start_time = datetime.now()
        self.page_count = 0
        self.error_count = 0
        self.crawled_urls = []
        self.error_urls = []

    def register_page_crawled(self, url):
        self.page_count += 1
        self.crawled_urls.append(url)

    def register_error(self, url, error):
        self.error_count += 1
        self.error_urls.append((url, str(error)))

    def generate_report(self):
        end_time = datetime.now()
        duration = end_time - self.start_time

        report_data = {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': str(duration),
            'total_pages_crawled': self.page_count,
            'total_errors': self.error_count,
            'crawled_urls': self.crawled_urls,
            'error_urls': self.error_urls
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if self.report_format == 'json':
            filename = os.path.join(self.output_directory, f'crawl_report_{timestamp}.json')
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=4)
            print(f"Report generated: {filename}")
        else:
            filename = os.path.join(self.output_directory, f'crawl_report_{timestamp}.txt')
            with open(filename, 'w') as f:
                f.write(f"Crawl Report\n")
                f.write(f"Start Time: {self.start_time}\n")
                f.write(f"End Time: {end_time}\n")
                f.write(f"Duration: {duration}\n")
                f.write(f"Total Pages Crawled: {self.page_count}\n")
                f.write(f"Total Errors: {self.error_count}\n\n")

                if self.crawled_urls:
                    f.write("Crawled URLs:\n")
                    for url in self.crawled_urls:
                        f.write(f"- {url}\n")
                    f.write("\n")

                if self.error_urls:
                    f.write("Error URLs:\n")
                    for url, error in self.error_urls:
                        f.write(f"- {url}: {error}\n")
            print(f"Report generated: {filename}")

    def save_chunk(self, chunk, chunk_number):
        if not chunk:
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sanitized_base_url = sanitize_filename(chunk[0]['base_url']) if chunk else 'unknown_base_url'
        filename = os.path.join(self.output_directory, f'crawled_data_{sanitized_base_url}_{timestamp}_chunk{chunk_number}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=4, ensure_ascii=False)
        print(f"Saved chunk {chunk_number} to {filename}")
        