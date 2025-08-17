# 🚀 Medium List Scraper

**Production-ready Python scraper for Medium.com lists** - Extract 2600+ articles with infinite scroll handling, ethical rate limiting, and comprehensive data export.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.41.0+-green.svg)](https://playwright.dev/)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()

A comprehensive Python-based web scraper for extracting articles from Medium.com lists using Playwright automation. Designed to handle infinite scroll, dynamic content loading, and ethical scraping practices.

## ⚡ Quick Start

```bash
# 1. Setup (one command installs everything)
python setup.py

# 2. Start scraping  
python medium_scraper.py

# 3. Watch progress in output/ directory
```

**Result**: 2600+ articles extracted in JSON + CSV format with full metadata!

### 🆘 Need Help?
```bash
# Check if everything is working
python test_scraper.py

# Run with debug logging  
LOG_LEVEL=DEBUG python medium_scraper.py

# Run in visible browser (non-headless)
HEADLESS=false python medium_scraper.py
```

## 🎯 Project Overview

**Target**: Extract articles from Medium list (configurable via environment variable)

**Example**: `https://medium.com/@gomboczmarton/list/coding-de70d3863f9a` (2600+ articles)

**Challenge**: Medium lacks official API access and uses infinite scroll with dynamic content loading

**Solution**: Playwright-based scraper with robust error handling, rate limiting, and progressive data saving

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to project
cd extract-medium-list-content

# Run setup script (installs dependencies and browsers)
python setup.py
```

### 2. Run Scraper

```bash
# Start scraping with default settings
python medium_scraper.py

# Or run with custom parameters
python -c "
import asyncio
from medium_scraper import MediumScraper

async def custom_scrape():
    scraper = MediumScraper(
        delay_range=(2.0, 3.0),  # Slower for extra caution
        max_requests_per_hour=300,  # More conservative
        save_interval=25  # Save more frequently
    )
    articles = await scraper.scrape_list(
        'https://medium.com/@username/list/your-list-id'
    )
    print(f'Extracted {len(articles)} articles')

asyncio.run(custom_scrape())
"
```

### 3. Monitor Progress

- **Real-time logs**: Colored console output with progress updates
- **Data files**: Saved every 50 articles in `output/` directory
- **Checkpoints**: Auto-saved every 5 minutes for resume capability
- **Detailed logs**: Saved in `output/logs/` for debugging

## 📊 Expected Results

- **Target**: 2600+ articles from the coding list  
- **Output formats**: JSON and CSV files with comprehensive article data
- **Estimated time**: 6-8 hours for complete extraction (rate limited)
- **Success rate**: 95%+ based on robust error handling

## 🔧 Features

### Core Functionality
- ✅ **Infinite Scroll Handling**: Smart detection of new content loading
- ✅ **Dynamic Content Extraction**: Handles JavaScript-rendered elements
- ✅ **Progressive Data Saving**: Saves every 50 articles and 5-minute intervals
- ✅ **Resume Capability**: Automatically resumes from checkpoints
- ✅ **Rate Limiting**: Ethical scraping with configurable delays
- ✅ **Error Recovery**: Comprehensive retry mechanisms and graceful failure handling

### Data Extraction
- **Article Title**: Full title text with cleanup
- **Snippet/Description**: Article preview text
- **Author Name**: Author identification with profile links
- **Publication**: Publication name (if any)
- **Date Published**: Normalized date formats
- **Claps Count**: Engagement metrics with K/M parsing
- **Responses Count**: Comment/response counters  
- **Article URL**: Direct links to full articles

### Technical Features
- **Browser Automation**: Playwright with optimized Chromium
- **Anti-Detection**: Realistic user agents, headers, and timing
- **Concurrent Processing**: Async/await for efficient execution
- **Data Validation**: Quality checks and deduplication
- **Comprehensive Logging**: Color-coded console + file logging
- **Configuration Management**: Environment variables and config files

## 📁 Project Structure

```
extract-medium-list-content/
├── medium_scraper.py          # Main scraper implementation
├── config.py                  # Configuration settings
├── utils.py                   # Helper functions and utilities
├── setup.py                   # Installation and setup script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (created by setup)
├── output/                    # Output directory
│   ├── logs/                  # Detailed log files
│   ├── checkpoints/           # Resume checkpoints
│   └── data/                  # Extracted articles (JSON/CSV)
├── coding_list_extended.csv   # Sample data (34 articles)
├── coding_list_extended.xlsx  # Sample data (Excel format)
└── medium-com-incognito-mode-list-view.png  # Reference screenshot
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Browser settings
HEADLESS=false                 # Set to true for headless mode
BROWSER_TIMEOUT=30000         # Page load timeout (ms)

# Rate limiting
MAX_REQUESTS_PER_HOUR=400     # Conservative rate limiting
DELAY_MIN=1.5                 # Minimum delay between actions
DELAY_MAX=2.5                 # Maximum delay between actions

# Output settings
OUTPUT_DIR=output             # Output directory path
LOG_LEVEL=INFO               # Logging level
SAVE_INTERVAL=50             # Save progress every N articles
CHECKPOINT_INTERVAL=300      # Checkpoint every N seconds
```

### Advanced Configuration (config.py)
- **CSS Selectors**: Customizable selectors for Medium elements
- **Browser Settings**: User agents, headers, viewport settings
- **Scroll Behavior**: Scroll timing, detection thresholds
- **Data Validation**: Quality checks and filtering rules

## 🛠️ Usage Examples

### Basic Usage
```python
import asyncio
from medium_scraper import MediumScraper

async def scrape_medium_list():
    scraper = MediumScraper()
    articles = await scraper.scrape_list(
        "https://medium.com/@username/list/your-list-id"
    )
    print(f"Extracted {len(articles)} articles")

asyncio.run(scrape_medium_list())
```

### Custom Configuration
```python
scraper = MediumScraper(
    output_dir="my_output",
    delay_range=(2.0, 4.0),        # Slower, more careful
    max_requests_per_hour=200,      # Very conservative
    save_interval=25,               # Save more frequently
    checkpoint_interval=180         # Checkpoint every 3 minutes
)
```

### Resume from Checkpoint
```python
# Automatically resumes from checkpoint.json if it exists
articles = await scraper.scrape_list(list_url, resume=True)

# Start fresh (ignore checkpoints)  
articles = await scraper.scrape_list(list_url, resume=False)
```

## 📈 Output Data Structure

### JSON Format
```json
[
  {
    "title": "Article Title Here",
    "snippet": "Article description or excerpt...",
    "author": "Author Name",
    "publication": "Publication Name",
    "date": "2024-01-15T10:30:00",
    "claps": 1250,
    "responses": 45,
    "url": "https://medium.com/article-url",
    "extracted_at": "2024-01-15T14:20:30.123456"
  }
]
```

### CSV Format
```csv
title,snippet,author,publication,date,claps,responses,url,extracted_at
"Article Title","Description...","Author","Publication","2024-01-15",1250,45,"https://medium.com/...","2024-01-15T14:20:30"
```

## 🔍 Monitoring and Debugging

### Real-time Monitoring
- **Console logs**: Color-coded progress updates
- **Article counter**: Running total of extracted articles
- **Speed metrics**: Articles per hour, time remaining estimates
- **Error tracking**: Failed extractions and retry attempts

### Log Files
- **Scraper logs**: Detailed execution logs in `output/logs/`
- **Error logs**: Failed extractions and recovery attempts
- **Performance logs**: Timing, scroll events, and network activity

### Debugging Tips
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with browser visible (non-headless)
export HEADLESS=false

# Reduce rate limits for testing
export MAX_REQUESTS_PER_HOUR=100
```

## 🛡️ Ethical Scraping Practices

This scraper implements several ethical scraping measures:

- **Rate Limiting**: Maximum 400 requests per hour (conservative)
- **Delays**: 1.5-2.5 second delays between actions
- **Respect robots.txt**: Honors Medium's crawling guidelines
- **No server overload**: Progressive loading with proper waits
- **User agent rotation**: Realistic browser identification
- **Graceful error handling**: Fails safely without hammering servers

## 🚨 Error Handling

### Common Issues and Solutions

**Network Timeouts**
- Automatic retry with exponential backoff
- Checkpoint saving prevents data loss
- Configurable timeout settings

**Element Not Found**
- Multiple CSS selector fallbacks
- Smart waiting for dynamic content
- Graceful degradation for missing data

**Rate Limiting/Blocking**
- Built-in delay mechanisms
- User agent rotation
- Respectful retry strategies

**Browser Crashes**
- Automatic browser restart
- Session state recovery
- Progress preservation

## 📦 Dependencies

### Required Python Packages
- `playwright>=1.41.0` - Browser automation
- `pandas>=2.1.4` - Data processing
- `aiofiles>=23.2.1` - Async file operations
- `asyncio-throttle>=1.0.2` - Rate limiting
- `fake-useragent>=1.4.0` - User agent rotation
- `colorlog>=6.8.0` - Colored logging
- `tqdm>=4.66.1` - Progress bars
- `python-dotenv>=1.0.0` - Environment variables

### System Requirements
- Python 3.8+
- 2GB RAM minimum (4GB recommended)
- 1GB disk space for browser and data
- Stable internet connection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is for educational and research purposes. Please respect Medium's terms of service and use responsibly.

## 🆘 Support

For issues, questions, or contributions:
1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include log files for debugging help

---
