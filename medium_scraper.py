#!/usr/bin/env python3
"""
Medium List Scraper using Playwright

A comprehensive scraper for extracting articles from Medium lists with infinite scroll support.
Designed for ethical scraping with rate limiting, error handling, and progressive data saving.

Target: https://medium.com/@gomboczmarton/list/coding-de70d3863f9a
Goal: Extract all 2600+ articles from the coding list
"""

import asyncio
import json
import csv
import logging
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse

import pandas as pd
import aiofiles
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from fake_useragent import UserAgent
from asyncio_throttle import Throttler
import colorlog
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import configuration
from config import ScrapingConfig

@dataclass
class Article:
    """Data structure for Medium articles"""
    title: str
    snippet: str
    author: str
    publication: str
    date: str
    claps: int
    responses: int
    url: str
    extracted_at: str

class MediumScraper:
    """
    Comprehensive Medium list scraper with Playwright
    
    Features:
    - Infinite scroll handling with smart detection
    - Progressive data saving (JSON/CSV)
    - Rate limiting and ethical scraping
    - Comprehensive error handling
    - Resume capability from checkpoints
    - Detailed logging and monitoring
    """
    
    def __init__(self, 
                 output_dir: str = "output",
                 delay_range: Tuple[float, float] = (1.0, 2.0),
                 max_requests_per_hour: int = 500,
                 save_interval: int = 100,
                 checkpoint_interval: int = 300):  # 5 minutes
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Rate limiting and timing
        self.delay_range = delay_range
        self.max_requests_per_hour = max_requests_per_hour
        self.save_interval = save_interval
        self.checkpoint_interval = checkpoint_interval
        
        # Data storage
        self.articles: List[Article] = []
        self.scraped_urls: set = set()
        self.start_time = datetime.now()
        self.last_save_time = datetime.now()
        self.last_checkpoint_time = datetime.now()
        
        # Browser setup
        self.browser: Optional[Browser] = None
        
        # CSS Selectors
        self.selectors = ScrapingConfig.SELECTORS
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.ua = UserAgent()
        
        # Throttling
        self.throttler = Throttler(rate_limit=max_requests_per_hour, period=3600)
        
        # Setup logging
        self._setup_logging()
        
        # Selectors based on Medium's current structure
        self.selectors = {
            'article_container': 'article',
            'title': 'h2',  # Main title is always in h2
            'snippet': 'h3',  # Snippet is in h3
            'author_link': 'a[href*="@"]',  # Author links contain @
            'publication': 'a[href*="medium.com/"]:not([href*="@"])',  # First non-author link
            'date': 'time',
            'claps': '[data-testid="clapCount"], .l',
            'responses': '[data-testid="responsesCount"], .pw-responses',
            'article_link_container': '[data-href]'  # Container with data-href
        }
    
    def _setup_logging(self):
        """Configure comprehensive logging with colors"""
        
        # Create logs directory
        logs_dir = self.output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configure colored console logging
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))
        
        # Configure file logging
        file_handler = logging.FileHandler(
            logs_dir / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        
        # Setup logger
        self.logger = logging.getLogger("MediumScraper")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Suppress playwright logs
        logging.getLogger("playwright").setLevel(logging.WARNING)
    
    async def _init_browser(self) -> None:
        """Initialize Playwright browser with optimized settings"""
        
        self.logger.info("Initializing browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with optimized settings
        # Use headless=False for better scroll behavior with Medium's infinite scroll
        headless_mode = os.getenv('HEADLESS', 'false').lower() == 'true'  # Default to visible
        self.logger.debug(f"Browser headless mode: {headless_mode}")
        
        self.browser = await playwright.firefox.launch(
            headless=headless_mode
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
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
        )
        
        # Create page
        self.page = await self.context.new_page()
        
        # Set realistic navigation timeout
        self.page.set_default_timeout(30000)
        
        self.logger.info("Browser initialized successfully")
    
    async def _navigate_to_list(self, list_url: str) -> bool:
        """Navigate to Medium list with error handling"""
        
        self.logger.info(f"Navigating to: {list_url}")
        
        try:
            async with self.throttler:
                response = await self.page.goto(
                    list_url, 
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                
                if response.status != 200:
                    self.logger.error(f"Failed to load page. Status: {response.status}")
                    return False
                
                # Wait for content to load
                await self.page.wait_for_selector(self.selectors['article_container'], timeout=15000)
                
                # Random delay to appear more human-like
                await asyncio.sleep(2 + (time.time() % 2))
                
                self.logger.info("Successfully navigated to list page")
                return True
                
        except Exception as e:
            self.logger.error(f"Navigation failed: {str(e)}")
            return False
    
    async def _extract_article_data(self, article_element) -> Optional[Article]:
        """Extract data from a single article element with robust error handling"""
        
        try:
            # Extract title
            title_elem = await article_element.query_selector(self.selectors['title'])
            title = await title_elem.inner_text() if title_elem else "No title"
            title = title.strip()
            
            # Extract snippet
            snippet_elem = await article_element.query_selector(self.selectors['snippet'])
            snippet = await snippet_elem.inner_text() if snippet_elem else ""
            snippet = snippet.strip()
            
            # Extract author
            author_elem = await article_element.query_selector(self.selectors['author_link'])
            author = ""
            if author_elem:
                author_text = await author_elem.inner_text()
                author_text = author_text.strip()
                author_href = await author_elem.get_attribute('href') or ""
                if '@' in author_href:
                    author = author_text
                else:
                    author = author_text.split('\n')[0] if author_text else ""
            
            # Extract publication
            pub_elem = await article_element.query_selector(self.selectors['publication'])
            publication = await pub_elem.inner_text() if pub_elem else ""
            publication = publication.strip()
            
            # Extract date
            date_elem = await article_element.query_selector(self.selectors['date'])
            date = ""
            if date_elem:
                date_attr = await date_elem.get_attribute('datetime')
                if date_attr:
                    date = date_attr
                else:
                    date_text = await date_elem.inner_text()
                    date = date_text.strip()
            
            # Extract claps - need to parse the middle number from '.l' element
            claps = 0
            claps_elem = await article_element.query_selector(self.selectors['claps'])
            if claps_elem:
                claps_text = await claps_elem.inner_text()
                claps = self._parse_claps(claps_text.strip())
            
            # Extract responses
            responses = 0
            responses_elem = await article_element.query_selector(self.selectors['responses'])
            if responses_elem:
                responses_text = await responses_elem.inner_text()
                responses = self._parse_number(responses_text.strip())
            
            # Extract article URL from data-href attribute
            url = ""
            url_elem = await article_element.query_selector(self.selectors['article_link_container'])
            if url_elem:
                data_href = await url_elem.get_attribute('data-href')
                if data_href:
                    if data_href.startswith('/'):
                        url = f"https://medium.com{data_href}"
                    elif data_href.startswith('http'):
                        url = data_href
                    else:
                        url = urljoin("https://medium.com", data_href)
            
            # Note: URL checking is now done before calling this function
            
            article = Article(
                title=title,
                snippet=snippet,
                author=author,
                publication=publication,
                date=date,
                claps=claps,
                responses=responses,
                url=url,
                extracted_at=datetime.now().isoformat()
            )
            
            self.scraped_urls.add(url)
            return article
            
        except Exception as e:
            self.logger.warning(f"Failed to extract article data: {str(e)}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """Parse simple numbers with K, M suffixes"""
        
        if not text:
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
    
    def _parse_claps(self, text: str) -> int:
        """Parse claps from Medium's .l element format: 'date\\nclaps\\nresponses'"""
        
        if not text:
            return 0
        
        try:
            # Split by newlines and look for the clap number
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Typical format: ['1d ago', '146', '2'] or ['Jun 24', '238', '7']
            if len(lines) >= 3:
                # The clap count is typically the second number (index 1)
                middle_line = lines[1]
                if middle_line.isdigit():
                    return int(middle_line)
            
            # If exactly 3 lines, middle is claps
            if len(lines) == 3:
                for i, line in enumerate(lines):
                    if line.isdigit() and i == 1:  # Middle line
                        return int(line)
            
            # Fallback: find the largest number that's not too small (likely not response count)
            numbers = [int(match) for match in re.findall(r'\d+', text) if int(match) >= 10]
            if numbers:
                return max(numbers)  # Return the largest number as claps
            
            return 0
            
        except (ValueError, TypeError):
            return 0
    
    async def _scroll_and_load_content(self, existing_articles: List[Article] = None) -> List[Article]:
        """Handle infinite scroll and extract articles progressively"""
        
        self.logger.info("Starting infinite scroll content extraction...")
        
        # Start with existing articles if provided
        articles_found = existing_articles.copy() if existing_articles else []
        consecutive_no_new_content = 0
        consecutive_all_known_content = 0  # Track when ALL articles are already known
        consecutive_no_scroll_progress = 0  # Track when page stops loading new elements
        scroll_attempts = 0
        last_article_count = 0
        max_consecutive_empty = 5
        # Dynamic limit based on existing articles
        existing_count = len(articles_found) if existing_articles else 0
        estimated_scrolls_needed = max(200, existing_count // 15 + 100)  # 15 articles/scroll estimate
        max_consecutive_all_known = estimated_scrolls_needed
        
        self.logger.info(f"Dynamic scroll limit: {max_consecutive_all_known} (based on {existing_count} existing articles)")
        max_scroll_attempts = 5000  # Much higher safety limit for large lists
        
        while consecutive_no_new_content < max_consecutive_empty and consecutive_all_known_content < max_consecutive_all_known and scroll_attempts < max_scroll_attempts:
            
            # Get current articles on page
            current_articles = await self.page.query_selector_all(self.selectors['article_container'])
            initial_count = len(articles_found)
            
            self.logger.info(f"Found {len(current_articles)} article elements on page")
            
            # Extract data from articles
            articles_extracted = 0
            articles_already_known = 0
            articles_failed = 0
            
            for article_element in current_articles:
                try:
                    # First check if we can extract URL to determine if it's known
                    url_elem = await article_element.query_selector(self.selectors['article_link_container'])
                    if url_elem:
                        data_href = await url_elem.get_attribute('data-href')
                        if data_href:
                            if data_href.startswith('/'):
                                url = f"https://medium.com{data_href}"
                            elif data_href.startswith('http'):
                                url = data_href
                            else:
                                url = f"https://medium.com/{data_href}"
                            
                            # Check if this URL is already known
                            if url in self.scraped_urls:
                                articles_already_known += 1
                                continue  # Skip extraction for known articles
                    
                    # Extract full article data for new articles
                    article_data = await self._extract_article_data(article_element)
                    if article_data and article_data.url not in [a.url for a in articles_found]:
                        articles_found.append(article_data)
                        articles_extracted += 1
                        self.logger.info(f"Extracted NEW: {article_data.title[:50]}...")
                    else:
                        articles_failed += 1
                        
                except Exception as e:
                    articles_failed += 1
                    self.logger.debug(f"Article processing failed: {str(e)}")
            
            new_articles_count = len(articles_found) - initial_count
            
            # Check for actual end of list (no new elements loaded)
            if len(current_articles) == last_article_count:
                consecutive_no_scroll_progress += 1
            else:
                consecutive_no_scroll_progress = 0
                last_article_count = len(current_articles)
            
            # Enhanced logging with detailed stats
            self.logger.info(f"Scroll {scroll_attempts + 1}: Found {len(current_articles)} elements → "
                           f"New: {articles_extracted}, Known: {articles_already_known}, Failed: {articles_failed}"
                           f" (No progress: {consecutive_no_scroll_progress})")
            
            # Smart stopping logic
            if new_articles_count == 0:
                if articles_already_known > 0:
                    # We found articles, but they're all already known - continue scrolling
                    consecutive_all_known_content += 1
                    consecutive_no_new_content = 0  # Reset since we found recognizable content
                    self.logger.info(f"All {articles_already_known} articles already known. Continue scrolling... ({consecutive_all_known_content}/{max_consecutive_all_known})")
                else:
                    # Truly no articles found (extraction failed or really empty)
                    consecutive_no_new_content += 1
                    consecutive_all_known_content = 0
                    self.logger.warning(f"No articles extracted. Consecutive failures: {consecutive_no_new_content}/{max_consecutive_empty}")
            else:
                # Found new articles - reset both counters
                consecutive_no_new_content = 0
                consecutive_all_known_content = 0
                self.logger.info(f"✅ Found {new_articles_count} NEW articles! Total: {len(articles_found)}")
            
            # Progressive saving
            if len(articles_found) % self.save_interval == 0:
                await self._save_progress(articles_found)
            
            # Checkpoint saving when new content is added
            if new_articles_count > 0 and len(articles_found) > 0:
                await self._save_checkpoint(articles_found)
                self.logger.debug(f"Checkpoint updated: {len(articles_found)} total articles")
            
            # Check if we've reached the end
            if consecutive_no_scroll_progress >= 10:
                self.logger.info("Reached ACTUAL end of content (no new elements loaded for 10 scrolls)")
                break
            elif consecutive_no_new_content >= max_consecutive_empty:
                self.logger.info("Reached end of content (no articles could be extracted)")
                break
            elif consecutive_all_known_content >= max_consecutive_all_known:
                self.logger.warning(f"Reached scroll limit ({max_consecutive_all_known}) - may not have reached actual end")
                self.logger.warning(f"Consider increasing max_consecutive_all_known if more articles expected")
                break
            
            # Scroll down to load more content
            scroll_attempts += 1
            
            # Adaptive scrolling: faster when all content is known
            if articles_already_known > 0 and articles_extracted == 0:
                # Fast scroll through known content
                await self._perform_fast_scroll()
                await asyncio.sleep(2)  # Longer wait for loading
                self.logger.debug("Fast-scrolling through known content...")
            else:
                # Normal scroll for new content
                await self._perform_scroll()
                await asyncio.sleep(3)  # Longer wait for loading
            
            # Check for loading indicators
            await self._wait_for_loading_complete()
        
        self.logger.info(f"Scroll extraction completed. Total articles: {len(articles_found)}")
        return articles_found
    
    async def _perform_scroll(self):
        """Perform scroll action with human-like behavior"""
        
        try:
            # Get page height before scroll
            previous_height = await self.page.evaluate("document.body.scrollHeight")
            
            # Scroll to bottom
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Random delay between scrolls (1-2 seconds)
            delay = self.delay_range[0] + (self.delay_range[1] - self.delay_range[0]) * (time.time() % 1)
            await asyncio.sleep(delay)
            
            # Check if new content loaded
            new_height = await self.page.evaluate("document.body.scrollHeight")
            
            if new_height == previous_height:
                self.logger.debug("No height change detected after scroll")
            else:
                self.logger.debug(f"Page height changed: {previous_height} -> {new_height}")
                
        except Exception as e:
            self.logger.warning(f"Scroll action failed: {str(e)}")
    
    async def _perform_fast_scroll(self):
        """Perform faster scroll when going through known content"""
        
        try:
            # Get current position
            current_pos = await self.page.evaluate("window.pageYOffset")
            
            # Scroll by larger chunks (multiple screens)
            scroll_distance = 2000  # 2000px at once
            new_pos = current_pos + scroll_distance
            
            await self.page.evaluate(f"window.scrollTo(0, {new_pos})")
            
            # Shorter delay for fast scrolling
            await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.warning(f"Fast scroll action failed: {str(e)}")
    
    async def _wait_for_loading_complete(self):
        """Wait for loading indicators to disappear and network to be idle"""
        
        try:
            # Wait for any network requests to settle
            await asyncio.sleep(2)
            
            # Check for actual content changes
            initial_height = await self.page.evaluate("document.body.scrollHeight")
            await asyncio.sleep(2)
            final_height = await self.page.evaluate("document.body.scrollHeight")
            
            if final_height > initial_height:
                self.logger.debug(f"Content loaded: {initial_height} -> {final_height}")
            else:
                self.logger.debug(f"No new content detected")
                
        except Exception as e:
            self.logger.debug(f"Loading wait error: {str(e)}")
    
    async def _save_progress(self, articles: List[Article]):
        """Save current progress to JSON and CSV files"""
        
        if not articles:
            return
        
        self.logger.info(f"Saving progress: {len(articles)} articles")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_path = self.output_dir / f"medium_articles_{timestamp}.json"
        json_data = [asdict(article) for article in articles]
        
        async with aiofiles.open(json_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(json_data, indent=2, ensure_ascii=False))
        
        # Save to CSV
        csv_path = self.output_dir / f"medium_articles_{timestamp}.csv"
        df = pd.DataFrame(json_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        self.logger.info(f"Progress saved to {json_path} and {csv_path}")
        self.last_save_time = datetime.now()
    
    async def _save_checkpoint(self, articles: List[Article]):
        """Save checkpoint for resume capability"""
        
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(articles),
            'scraped_urls': list(self.scraped_urls),
            'articles': [asdict(article) for article in articles]
        }
        
        checkpoint_path = self.output_dir / "checkpoint.json"
        
        async with aiofiles.open(checkpoint_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(checkpoint_data, indent=2, ensure_ascii=False))
        
        self.logger.info(f"Checkpoint saved: {len(articles)} articles")
    
    async def _load_checkpoint(self) -> List[Article]:
        """Load previous checkpoint if exists"""
        
        checkpoint_path = self.output_dir / "checkpoint.json"
        
        if not checkpoint_path.exists():
            self.logger.info("No checkpoint found, starting fresh")
            return []
        
        try:
            async with aiofiles.open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.loads(await f.read())
            
            articles = [Article(**article_data) for article_data in checkpoint_data['articles']]
            self.scraped_urls = set(checkpoint_data['scraped_urls'])
            
            self.logger.info(f"Loaded checkpoint: {len(articles)} articles")
            return articles
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {str(e)}")
            return []
    
    async def scrape_list(self, list_url: str, resume: bool = True) -> List[Article]:
        """Main scraping method"""
        
        self.logger.info(f"Starting Medium list scraping: {list_url}")
        self.logger.info(f"Target: Extract all articles from the coding list")
        self.logger.info(f"Settings: Delay {self.delay_range}s, Max {self.max_requests_per_hour} req/h")
        
        # Load checkpoint if resume is enabled
        articles = []
        if resume:
            articles = await self._load_checkpoint()
            if articles:
                self.logger.info(f"📊 RESUME: Starting with {len(articles)} existing articles from checkpoint")
                self.logger.info(f"🎯 TARGET: Need {max(0, 2600 - len(articles))} more articles to reach goal")
                if len(articles) >= 10:
                    self.logger.info(f"🔄 PROGRESS: Last article was '{articles[-1].title[:60]}...'")
        
        initial_article_count = len(articles)
        
        try:
            # Initialize browser
            await self._init_browser()
            
            # Navigate to list
            if not await self._navigate_to_list(list_url):
                self.logger.error("Failed to navigate to list")
                return articles
            
            # Scrape articles with infinite scroll (pass existing articles for progress tracking)
            scraped_articles = await self._scroll_and_load_content(existing_articles=articles)
            
            # Merge with existing articles (avoid duplicates)
            existing_urls = {article.url for article in articles}
            new_articles = [article for article in scraped_articles if article.url not in existing_urls]
            
            articles.extend(new_articles)
            
            # Final save
            await self._save_progress(articles)
            
            # Final checkpoint with all articles (old + new)
            await self._save_checkpoint(articles)
            
            # Final progress update
            new_articles_found = len(articles) - initial_article_count
            if new_articles_found > 0:
                self.logger.info(f"🎉 SUCCESS: Found {new_articles_found} new articles in this session!")
                self.logger.info(f"📈 PROGRESS: {initial_article_count} → {len(articles)} total articles")
            else:
                self.logger.info(f"ℹ️  No new articles found in this session")
            
            # Generate summary
            self._generate_summary(articles)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            raise
            
        finally:
            await self._cleanup()
    
    def _generate_summary(self, articles: List[Article]):
        """Generate scraping summary and statistics"""
        
        if not articles:
            self.logger.warning("No articles to summarize")
            return
        
        total_time = datetime.now() - self.start_time
        
        # Calculate statistics
        total_articles = len(articles)
        unique_authors = len(set(article.author for article in articles if article.author))
        unique_publications = len(set(article.publication for article in articles if article.publication))
        total_claps = sum(article.claps for article in articles)
        total_responses = sum(article.responses for article in articles)
        
        # Generate summary
        summary = f"""
        
=== SCRAPING SUMMARY ===
Total Articles Extracted: {total_articles}
Unique Authors: {unique_authors}
Unique Publications: {unique_publications}
Total Claps: {total_claps:,}
Total Responses: {total_responses:,}
Execution Time: {total_time}
Average Articles per Hour: {total_articles / (total_time.total_seconds() / 3600):.1f}

=== TOP AUTHORS BY ARTICLE COUNT ===
"""
        
        # Top authors
        author_counts = {}
        for article in articles:
            if article.author:
                author_counts[article.author] = author_counts.get(article.author, 0) + 1
        
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for author, count in top_authors:
            summary += f"{author}: {count} articles\n"
        
        summary += "\n=== TOP ARTICLES BY CLAPS ===\n"
        
        # Top articles by claps
        top_claps = sorted(articles, key=lambda x: x.claps, reverse=True)[:10]
        for article in top_claps:
            summary += f"{article.claps:,} claps - {article.title[:60]}...\n"
        
        self.logger.info(summary)
        
        # Save summary to file
        summary_path = self.output_dir / f"scraping_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
    
    async def _cleanup(self):
        """Clean up browser resources"""
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            
            self.logger.info("Browser cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

async def main():
    """Main execution function"""
    
    # Configuration
    LIST_URL = "https://medium.com/@gomboczmarton/list/coding-de70d3863f9a"
    
    # Initialize scraper with ethical settings
    scraper = MediumScraper(
        output_dir="output",
        delay_range=(1.5, 2.5),  # 1.5-2.5 second delays
        max_requests_per_hour=400,  # Conservative rate limiting
        save_interval=50,  # Save every 50 articles
        checkpoint_interval=300  # Checkpoint every 5 minutes
    )
    
    try:
        # Start scraping
        articles = await scraper.scrape_list(LIST_URL, resume=True)
        
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Total articles extracted: {len(articles)}")
        print(f"📁 Output files saved in: {scraper.output_dir}")
        
        if articles:
            print(f"🎯 Target reached: {len(articles)}/2600+ articles")
            print(f"📈 Success rate: {(len(articles)/2600)*100:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        print("🔄 Progress has been saved and can be resumed")
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {str(e)}")
        print("🔄 Check logs for details and resume from checkpoint")

if __name__ == "__main__":
    asyncio.run(main())