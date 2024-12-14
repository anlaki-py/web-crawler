# Website Crawler

A Python-based web crawler that systematically browses and archives website content, saving the results in a structured JSON format.

## Features

- Full website crawling capability
- Domain-specific crawling (stays within the same domain)
- Structured data extraction including:
  - Page titles
  - Text content
  - Meta descriptions
  - Internal links
  - Timestamps
  - HTTP status codes
- JSON output format
- Rate limiting to prevent server overload
- Error handling and retry mechanisms
- Session management for optimized requests
- User-agent headers to prevent blocking

## Requirements

- Python 3.6+
- requests
- beautifulsoup4

## Installation

1. Clone this repository or download the script
2. Install required packages:
   ```
   pip install requests beautifulsoup4
   ```

## Usage

1. Run the script:
   ```
   python web_crawler.py
   ```
2. Enter the target website URL when prompted
3. The crawler will begin collecting data
4. Results will be saved in `crawled_data.json`

## Output Format

The script generates a JSON file with the following structure:

```json
{
    "base_url": "https://example.com",
    "crawl_date": "2024-12-14T10:00:00.000000",
    "total_pages": 42,
    "pages": [
        {
            "url": "https://example.com",
            "title": "Page Title",
            "text_content": "Page content...",
            "meta_description": "Page description",
            "links": ["https://example.com/page1"],
            "timestamp": "2024-12-14T10:00:00.000000",
            "status_code": 200
        }
    ]
}
```

## Best Practices

- Check robots.txt before crawling
- Respect website terms of service
- Adjust sleep time between requests if needed
- Monitor memory usage for large websites
- Back up data regularly
- Verify website permissions before crawling

## Limitations

- Only crawls within the same domain
- Basic rate limiting (1 second between requests)
- Memory usage may increase with large websites
- No support for JavaScript-rendered content
## License

[MIT License](LICENCE) - feel free to use this code for any purpose.

## Disclaimer

This tool is for educational purposes only. Always ensure you have permission to crawl a website and comply with the site's robots.txt file and terms of service.

## Future Improvements

- Add support for robots.txt parsing
- Implement advanced rate limiting
- Add support for JavaScript-rendered content
- Include image and media file downloading
- Add proxy support
- Implement concurrent crawling
- Add export options for different formats
- Include crawling progress bar
- Add resume capability for interrupted crawls

## Author

[anlaki](https://anlaki.carrd.co)
