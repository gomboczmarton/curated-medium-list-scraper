#!/usr/bin/env python3
"""
Utility functions for Medium List Scraper

This module contains helper functions for data processing,
validation, and common operations used throughout the scraper.
"""

import re
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse
import hashlib
import logging

def parse_number(text: str) -> int:
    """
    Parse claps/responses count from text, handling K, M suffixes
    
    Args:
        text: Text containing a number (e.g., "1.2K", "5M", "123")
        
    Returns:
        Parsed integer value
        
    Examples:
        >>> parse_number("1.2K")
        1200
        >>> parse_number("5M")
        5000000
        >>> parse_number("123")
        123
    """
    if not text or not isinstance(text, str):
        return 0
    
    # Remove non-numeric characters except K, M, and decimal points
    clean_text = re.sub(r'[^\d\.KMkm]', '', text.upper())
    
    if not clean_text:
        return 0
    
    try:
        if 'K' in clean_text:
            return int(float(clean_text.replace('K', '')) * 1000)
        elif 'M' in clean_text:
            return int(float(clean_text.replace('M', '')) * 1000000)
        else:
            return int(float(clean_text))
    except (ValueError, TypeError):
        return 0

def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text content
    
    Args:
        text: Raw text to clean
        max_length: Maximum length to truncate to
        
    Returns:
        Cleaned text string
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove extra whitespace and normalize
    cleaned = ' '.join(text.split())
    
    # Remove common artifacts
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces
    cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)  # Line breaks and tabs
    cleaned = cleaned.strip()
    
    # Truncate if needed
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + '...'
    
    return cleaned

def normalize_url(url: str, base_url: str = "https://medium.com") -> str:
    """
    Normalize and validate URLs
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative links
        
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Handle relative URLs
    if url.startswith('/'):
        return urljoin(base_url, url)
    
    # Handle protocol-relative URLs
    if url.startswith('//'):
        return f"https:{url}"
    
    # Return absolute URLs as-is
    if url.startswith(('http://', 'https://')):
        return url
    
    # Assume relative URL
    return urljoin(base_url, url)

def validate_article_data(article_data: Dict[str, Any]) -> bool:
    """
    Validate article data completeness and quality
    
    Args:
        article_data: Dictionary containing article information
        
    Returns:
        True if article data is valid, False otherwise
    """
    required_fields = ['title', 'url']
    
    # Check required fields
    for field in required_fields:
        if not article_data.get(field):
            return False
    
    # Validate title length
    title = article_data.get('title', '')
    if len(title.strip()) < 5:
        return False
    
    # Validate URL format
    url = article_data.get('url', '')
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False
    
    return True

def generate_article_hash(title: str, author: str, url: str) -> str:
    """
    Generate unique hash for article deduplication
    
    Args:
        title: Article title
        author: Article author
        url: Article URL
        
    Returns:
        SHA256 hash string
    """
    content = f"{title.lower().strip()}{author.lower().strip()}{url.lower().strip()}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def parse_medium_date(date_str: str) -> str:
    """
    Parse Medium date formats into ISO format
    
    Args:
        date_str: Date string from Medium
        
    Returns:
        ISO formatted date string
    """
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # Handle relative dates (e.g., "3 days ago", "1 week ago")
    relative_patterns = [
        (r'(\d+)\s*days?\s*ago', lambda m: (datetime.now() - timedelta(days=int(m.group(1)))).isoformat()),
        (r'(\d+)\s*weeks?\s*ago', lambda m: (datetime.now() - timedelta(weeks=int(m.group(1)))).isoformat()),
        (r'(\d+)\s*months?\s*ago', lambda m: (datetime.now() - timedelta(days=int(m.group(1))*30)).isoformat()),
        (r'yesterday', lambda m: (datetime.now() - timedelta(days=1)).isoformat()),
        (r'today|now', lambda m: datetime.now().isoformat()),
    ]
    
    for pattern, handler in relative_patterns:
        match = re.search(pattern, date_str.lower())
        if match:
            return handler(match)
    
    # Handle absolute dates
    date_formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%B %d, %Y',
        '%b %d, %Y',
        '%b %d',
        '%Y'
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            # If year is missing, assume current year
            if fmt == '%b %d':
                parsed_date = parsed_date.replace(year=datetime.now().year)
            return parsed_date.isoformat()
        except ValueError:
            continue
    
    # Return original string if parsing fails
    return date_str

def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate articles based on URL and content similarity
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Deduplicated list of articles
    """
    seen_urls = set()
    seen_hashes = set()
    unique_articles = []
    
    for article in articles:
        url = article.get('url', '')
        title = article.get('title', '')
        author = article.get('author', '')
        
        # Skip if URL already seen
        if url in seen_urls:
            continue
        
        # Skip if content hash already seen
        content_hash = generate_article_hash(title, author, url)
        if content_hash in seen_hashes:
            continue
        
        seen_urls.add(url)
        seen_hashes.add(content_hash)
        unique_articles.append(article)
    
    return unique_articles

def save_articles_to_json(articles: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Save articles to JSON file with error handling
    
    Args:
        articles: List of article dictionaries
        filepath: Path to save JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON to {filepath}: {str(e)}")
        return False

def save_articles_to_csv(articles: List[Dict[str, Any]], filepath: str, columns: Optional[List[str]] = None) -> bool:
    """
    Save articles to CSV file with error handling
    
    Args:
        articles: List of article dictionaries
        filepath: Path to save CSV file
        columns: Column order (optional)
        
    Returns:
        True if successful, False otherwise
    """
    if not articles:
        return False
    
    try:
        # Determine columns
        if not columns:
            columns = list(articles[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(articles)
        
        return True
    except Exception as e:
        logging.error(f"Failed to save CSV to {filepath}: {str(e)}")
        return False

def calculate_scraping_stats(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics from scraped articles
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Dictionary containing statistics
    """
    if not articles:
        return {}
    
    stats = {
        'total_articles': len(articles),
        'unique_authors': len(set(article.get('author', '') for article in articles if article.get('author'))),
        'unique_publications': len(set(article.get('publication', '') for article in articles if article.get('publication'))),
        'total_claps': sum(article.get('claps', 0) for article in articles),
        'total_responses': sum(article.get('responses', 0) for article in articles),
        'avg_claps': 0,
        'avg_responses': 0,
        'top_authors': {},
        'top_publications': {},
        'date_range': {}
    }
    
    # Calculate averages
    if stats['total_articles'] > 0:
        stats['avg_claps'] = stats['total_claps'] / stats['total_articles']
        stats['avg_responses'] = stats['total_responses'] / stats['total_articles']
    
    # Count by author
    author_counts = {}
    for article in articles:
        author = article.get('author', '')
        if author:
            author_counts[author] = author_counts.get(author, 0) + 1
    
    stats['top_authors'] = dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Count by publication
    pub_counts = {}
    for article in articles:
        pub = article.get('publication', '')
        if pub:
            pub_counts[pub] = pub_counts.get(pub, 0) + 1
    
    stats['top_publications'] = dict(sorted(pub_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return stats

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def is_valid_medium_url(url: str) -> bool:
    """
    Check if URL is a valid Medium article URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid Medium URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url.lower())
        
        # Check if it's a Medium domain
        valid_domains = ['medium.com', 'towardsdatascience.com', 'betterprogramming.pub']
        
        if any(domain in parsed.netloc for domain in valid_domains):
            return True
        
        # Check for custom Medium publications
        if parsed.netloc and 'medium.com' in url.lower():
            return True
            
        return False
        
    except Exception:
        return False