#!/usr/bin/env python3
"""
Configuration settings for Medium List Scraper

This file contains all configurable parameters for the scraper,
allowing easy customization without modifying the main code.
"""

import os
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ScrapingConfig:
    """Main configuration class for the Medium scraper"""
    
    # Target URLs
    DEFAULT_LIST_URL = os.getenv('MEDIUM_LIST_URL', 'https://medium.com/@username/list/your-list-id')
    
    # Output settings
    OUTPUT_DIR = "output"
    LOGS_DIR = "logs"
    
    # Rate limiting and timing
    DELAY_RANGE: Tuple[float, float] = (1.5, 2.5)  # Seconds between actions
    MAX_REQUESTS_PER_HOUR = 400  # Conservative rate limiting
    SAVE_INTERVAL = 50  # Save progress every N articles
    CHECKPOINT_INTERVAL = 300  # Checkpoint every N seconds (5 minutes)
    
    # Browser settings
    HEADLESS = False  # Set to True for headless browsing
    BROWSER_TIMEOUT = 30000  # 30 seconds
    PAGE_LOAD_TIMEOUT = 15000  # 15 seconds
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # Scroll settings
    MAX_CONSECUTIVE_EMPTY_SCROLLS = 5  # Stop after N scrolls with no new content
    MAX_SCROLL_ATTEMPTS = 1000  # Safety limit for total scrolls
    SCROLL_DELAY_RANGE: Tuple[float, float] = (2.0, 3.0)  # Delay after each scroll
    
    # Data extraction settings
    MIN_TITLE_LENGTH = 5  # Minimum characters for valid title
    MAX_TITLE_LENGTH = 500  # Maximum characters for title
    MAX_SNIPPET_LENGTH = 1000  # Maximum characters for snippet
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # Seconds between retries
    
    # Logging settings
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    CONSOLE_LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CSS Selectors for Medium articles
    SELECTORS = {
        # Main article container
        'article_container': 'article, [data-testid="postPreview"]',
        
        # Title selectors (try multiple)
        'title': 'h2, h3[data-testid="card-title"], [data-testid="post-preview-title"], .graf--title',
        
        # Snippet/description
        'snippet': 'h3:not([data-testid="card-title"]), p[data-testid="card-description"], .graf--p, .postPreview-excerpt',
        
        # Author information
        'author_link': 'a[href*="@"], a[data-testid="authorName"], .postMetaInline-authorLockup a',
        'author_text': '[data-testid="authorName"], .ds-link, .postMetaInline-authorLockup',
        
        # Publication
        'publication': '[data-testid="publication-name"], .ay .bb, .postMetaInline-authorLockup .link',
        
        # Date
        'date': 'time, [data-testid="storyPublishDate"], .postMetaInline time',
        
        # Engagement metrics
        'claps': '[data-testid="clapCount"], .l, .multireads, .buttonSet .u-flex1',
        'responses': '[data-testid="responsesCount"], .pw-responses, .buttonSet button[aria-label*="responses"]',
        
        # Article link
        'article_link': 'h2 a, h3 a, [data-testid="post-preview-title"], a[data-testid="post-preview-title"]',
        
        # Loading indicators
        'loading_indicators': [
            '[data-testid="loading"]',
            '.loading',
            '.spinner',
            '[aria-label*="Loading"]',
            '.js-loadingIndicator'
        ]
    }
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    # HTTP headers
    HTTP_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

class ProxyConfig:
    """Configuration for proxy settings (if needed)"""
    
    ENABLE_PROXY = False
    PROXY_LIST = []  # Add proxy servers if needed
    PROXY_ROTATION = True
    PROXY_TIMEOUT = 10
    
class OutputConfig:
    """Configuration for output formats and file naming"""
    
    # File naming patterns
    JSON_FILENAME_PATTERN = "medium_articles_{timestamp}.json"
    CSV_FILENAME_PATTERN = "medium_articles_{timestamp}.csv"
    CHECKPOINT_FILENAME = "checkpoint.json"
    SUMMARY_FILENAME_PATTERN = "scraping_summary_{timestamp}.txt"
    LOG_FILENAME_PATTERN = "scraper_{timestamp}.log"
    
    # CSV output columns
    CSV_COLUMNS = [
        'title', 'snippet', 'author', 'publication', 'date',
        'claps', 'responses', 'url', 'extracted_at'
    ]
    
    # JSON output settings
    JSON_INDENT = 2
    JSON_ENSURE_ASCII = False

# Environment variable overrides
if os.getenv('HEADLESS'):
    ScrapingConfig.HEADLESS = os.getenv('HEADLESS').lower() == 'true'

if os.getenv('MAX_REQUESTS_PER_HOUR'):
    ScrapingConfig.MAX_REQUESTS_PER_HOUR = int(os.getenv('MAX_REQUESTS_PER_HOUR'))

if os.getenv('OUTPUT_DIR'):
    ScrapingConfig.OUTPUT_DIR = os.getenv('OUTPUT_DIR')

if os.getenv('LOG_LEVEL'):
    ScrapingConfig.LOG_LEVEL = os.getenv('LOG_LEVEL').upper()