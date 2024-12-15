import re
from urllib.parse import urlparse, urljoin

def is_valid_url(url, base_domain, base_path, include_patterns, exclude_patterns, exclude_exact):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False
    if not (parsed_url.netloc == base_domain or parsed_url.netloc.endswith(f".{base_domain}")):
        return False
    if not parsed_url.path.startswith(base_path):
        return False

    if exclude_exact:
        if any(pattern in url.lower() for pattern in exclude_exact):
            return False

    if include_patterns:
        if not any(re.search(pattern, url) for pattern in include_patterns):
            return False

    if exclude_patterns:
        if any(re.search(pattern, url) for pattern in exclude_patterns):
            return False

    return True

def resolve_url(base_url, url):
    return urljoin(base_url, url)

def sanitize_filename(filename):
    return re.sub(r'[^\w\-_\.]', '_', filename)
    