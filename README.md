# Web Crawler and GitHub Documentation Crawler

This repository contains two Python scripts for crawling web pages and GitHub repositories to extract and store relevant content. Below is a brief overview of each script's capabilities.

## 1. web_crawler.py

### Overview
The `web_crawler.py` script is designed to crawl a specified website, extract page content, and save the data in JSON format. It respects `robots.txt` rules and allows customization of crawl depth and chunk size.

### Features
- **Domain-Specific Crawling**: Crawls only the specified domain and path.
- **Robots.txt Compliance**: Respects the rules defined in the website's `robots.txt` file.
- **Chunked Output**: Saves crawled data in JSON chunks for easier processing.
- **Customizable Depth**: Allows setting a maximum crawl depth.
- **Exclusion Rules**: Excludes URLs with specific patterns (e.g., login pages, static assets).

### Usage
1. Run the script and provide the website URL.
2. Optionally, set the chunk size and maximum crawl depth.
3. The script will save the crawled data in the `web_crawled_data` directory.

---

## 2. gitHub_docs_crawler.py

### Overview
The `gitHub_docs_crawler.py` script is designed to crawl a GitHub repository, specifically targeting documentation files (e.g., `.md`, `.txt`, `.html`). It extracts file content and metadata, saving the data in JSON format.

### Features
- **GitHub API Integration**: Uses the GitHub API to fetch repository contents.
- **File Type Filtering**: Targets specific file extensions (e.g., `.md`, `.html`).
- **Rate Limit Handling**: Automatically pauses when GitHub API rate limits are approached.
- **Chunked Output**: Saves crawled data in JSON chunks for easier processing.
- **Customizable Depth**: Allows setting a maximum directory recursion depth.

### Usage
1. Run the script and provide the GitHub repository URL.
2. Optionally, provide a GitHub token for authenticated requests.
3. The script will save the crawled data in the `github_api_crawled_data` directory.

---

## Credits
- The GitHub Documentation Crawler is inspired by the original work by [rsain/GitHub-Crawler](https://github.com/rsain/GitHub-Crawler).
