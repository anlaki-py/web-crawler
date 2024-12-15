import argparse
from crawler.core import WebCrawler
from crawler.config import load_config
import logging

def main():
    parser = argparse.ArgumentParser(description="Advanced Web Crawler")
    parser.add_argument("start_urls", nargs="*", help="Starting URLs for the crawl")
    parser.add_argument("-c", "--config", help="Path to YAML configuration file")
    parser.add_argument("-d", "--max_depth", type=int, help="Maximum crawl depth")
    parser.add_argument("-m", "--max_pages", type=int, help="Maximum number of pages to crawl")
    parser.add_argument("--concurrency", type=int, help="Number of concurrent threads/processes")
    parser.add_argument("--chunk_size", type=int, help="Number of pages per chunk")
    parser.add_argument("--retry_attempts", type=int, help="Number of retry attempts for failed requests")
    parser.add_argument("--retry_delay", type=float, help="Delay between retry attempts in seconds")
    parser.add_argument("--respect_robots", action="store_true", help="Respect robots.txt")
    parser.add_argument("--timeout", type=float, help="Request timeout in seconds")
    parser.add_argument("--user_agent", help="Custom user agent string")
    parser.add_argument("-i", "--include", action='append', help="Include URL patterns (regex)")
    parser.add_argument("-e", "--exclude", action='append', help="Exclude URL patterns (regex)")
    parser.add_argument("-o", "--output_directory", help="Output directory for crawled data")
    parser.add_argument("-r", "--report_format", choices=['text', 'json'], help="Report format (text or json)")
    parser.add_argument("--auth_type", choices=['basic', 'form', 'oauth'], help="Authentication type")
    parser.add_argument("--auth_username", help="Username for authentication")
    parser.add_argument("--auth_password", help="Password for authentication")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    config = load_config(args.config, args)  # Load config, prioritizing CLI args

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    crawler = WebCrawler(config)
    crawler.crawl()

if __name__ == "__main__":
    main()
    