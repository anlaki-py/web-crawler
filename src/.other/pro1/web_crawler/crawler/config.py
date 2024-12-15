import yaml
import os
from argparse import Namespace

DEFAULT_CONFIG = {
    'crawl': {
        'max_depth': 5,
        'max_pages': None,
        'concurrency': 10,
        'chunk_size': 50,
        'retry_attempts': 3,
        'retry_delay': 2,
        'respect_robots': True,
        'timeout': 10,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'urls': {
        'start_urls': [],
        'include_patterns': [],
        'exclude_patterns': [],
         'exclude_exact': [
            # Language specific pages
            'lang=go', 'lang=node', 'lang=rest', 'lang=ruby',
            'lang=java', 'lang=javascript', 'lang=php', 'lang=typescript',
            '/france',

            # User interface elements
            '#',

            # Authentication and user pages
            '/login', '/signin', '/signup', '/register',
            '/logout', '/signout', '/auth/',
            '/password', '/reset', '/forgot',

            # Account and settings pages
            '/settings', '/profile', '/account', '/preferences',
            '/dashboard', '/admin', '/user/',

            # Common utility pages
            '/search', '/filter', '/sort',
            '/print', '/download', '/upload',
            '/raw/', '/blame/', '/commits/',

            # Social and interaction pages
            '/comment', '/like', '/share', '/follow',

            # Common API and technical paths
            '/graphql', '/webhook',
            '/feeds/', '/rss/', '/atom/',

            # Session and tracking related
            '/session', '/track', '/analytics',

            # Common GitHub-specific paths (if crawling GitHub)
            '/pulse/', '/network/', '/graphs/',
            '/issues/new', '/pull/', '/compare/',
            '/edit/', '/delete/', '/archive/',
            '/stargazers', '/subscribers', '/fork',

            # Documents (videos, photos, archives...)
            '.zip', '.pdf', '/assets/', '/documents/',
            '.png', '.webp', '.jpg', '.jpeg'
        ],
    },
    'output': {
        'directory': 'crawled_data',
        'report_format': 'text'
    },
    'authentication': {
        'type': None,  # 'basic', 'form', 'oauth'
        'username': None,
        'password': None,
        # Add other authentication related fields as needed
    },
    'extraction': {
        'rules': {}  # CSS selectors or XPath for data extraction
    }
}

def load_config(config_file=None, cli_args: Namespace = None):
    config = DEFAULT_CONFIG.copy()

    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            try:
                file_config = yaml.safe_load(f)
                if file_config:
                    config = update_dict(config, file_config)
            except yaml.YAMLError as e:
                print(f"Error parsing YAML config file: {e}")

    if cli_args:
        cli_config = {
            'crawl': {
                'max_depth': cli_args.max_depth,
                'max_pages': cli_args.max_pages,
                'concurrency': cli_args.concurrency,
                'chunk_size': cli_args.chunk_size,
                'retry_attempts': cli_args.retry_attempts,
                'retry_delay': cli_args.retry_delay,
                'respect_robots': cli_args.respect_robots,
                'timeout': cli_args.timeout,
                'user_agent': cli_args.user_agent
            },
            'urls': {
                'start_urls': cli_args.start_urls,
                'include_patterns': cli_args.include,
                'exclude_patterns': cli_args.exclude,

            },
            'output': {
                'directory': cli_args.output_directory,
                'report_format': cli_args.report_format
            },
            'authentication': {
                'type': cli_args.auth_type,
                'username': cli_args.auth_username,
                'password': cli_args.auth_password
            }
        }
        config = update_dict(config, cli_config)
    return config

def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_dict(d.get(k, {}), v)
        elif v is not None:  # Only update if the value is provided
            d[k] = v
    return d
