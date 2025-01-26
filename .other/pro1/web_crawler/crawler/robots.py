import requests
from urllib.parse import urlparse
import re

class RobotsParser:
    def __init__(self, url):
        self.base_url = url
        self.parsed_base_url = urlparse(self.base_url)
        self.robots_url = f"{self.parsed_base_url.scheme}://{self.parsed_base_url.netloc}/robots.txt"
        self.disallowed_paths = []
        self.allow_paths = []
        self.crawl_delay = None
        self.user_agent = '*'
        self.parse_robots()

    def parse_robots(self):
        try:
            response = requests.get(self.robots_url)
            response.raise_for_status()
            self.parse_rules(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching or parsing robots.txt: {e}")

    def parse_rules(self, content):
        relevant_block = False
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('User-agent:'):
                user_agent = line.split(':', 1)[1].strip()
            relevant_block = (agent == '*' or agent.lower() == 'python-requests' or agent == 'gemini_bot')
            if relevant_block == False:
                self.disallowed_paths = []
                self.allow_paths = []
                continue
            elif line.startswith('Disallow:'):
                if relevant_block:
                    path = line.split(':', 1)[1].strip()
                    if path:
                         self.disallowed_paths.append(path)
            elif line.startswith('Allow:'):
                 if relevant_block:
                    path = line.split(':', 1)[1].strip()
                    if path:
                        self.allow_paths.append(path)
            elif line.startswith('Crawl-delay:'):
                if relevant_block:
                    try:
                        self.crawl_delay = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass

    def is_allowed(self, url):
        parsed_url = urlparse(url)
        path = parsed_url.path

        for allow_path in self.allow_paths:
            if allow_path == '/' or path.startswith(allow_path):
                return True

        for disallow_path in self.disallowed_paths:
            if disallow_path == '/' or path.startswith(disallow_path):
                return False
        return True

    def get_crawl_delay(self):
        return self.crawl_delay
                