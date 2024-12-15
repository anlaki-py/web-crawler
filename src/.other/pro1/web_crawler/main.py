from crawler.core import WebCrawler
from crawler.config import load_config
import logging

def run_crawler(config_file='config.yaml'):
    config = load_config(config_file)
    crawler = WebCrawler(config)
    crawler.crawl()

if __name__ == "__main__":
    run_crawler()
    