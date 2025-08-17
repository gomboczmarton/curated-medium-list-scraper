# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository implements web scrapers to fetch Medium.com lists and extract their content for analysis. The project targets extracting 2600+ items from curated coding lists collected over years. Medium lacks official API access, requiring automated scraping solutions.

## Communication Guidelines

- Repository owner communicates in Hungarian
- All code, documentation, and artifacts must be written in English
- Comments, variable names, function names, and technical documentation in English only

## Current Analysis

**Sample Data**: ChatGPT Agent extracted 34 items from Medium.com coding list (incognito mode) before scrolling limitations. Data structure visible in `coding_list_extended.xlsx` and `medium-com-incognito-mode-list-view.png`.

**Target**: Extract full 2600+ item dataset from personal Medium coding list accumulated over years.

## Recommended Technology Stack

**Primary Solution**: Playwright + Python for dynamic scrolling and JavaScript rendering
**Alternatives**: Selenium (traditional), Firecrawl (AI-powered), Scrapy (large-scale)
**Proxy Strategy**: Residential proxies (400-600 IPs) for rate limiting compliance
**CAPTCHA Handling**: 2Captcha/AntiCaptcha integration when needed
**Rate Limiting**: 1-2 second delays, max 500 requests/hour per IP

## Scraping Challenges

- Medium implements infinite scroll with AJAX loading
- Behavioral analysis for bot detection
- IP blocking and rate limiting
- No official API, unofficial APIs require subscriptions
- Requires handling of dynamic content and JavaScript execution

## Planned Subagents

1. **Scraper Agent**: Handle web scraping, scrolling, content extraction
2. **Proxy Manager Agent**: Manage IP rotation and rate limiting
3. **Data Processor Agent**: Parse extracted content, format for analysis
4. **CAPTCHA Solver Agent**: Handle anti-bot measures when encountered
5. **Analysis Agent**: Process collected data, generate insights and visualizations

## ✅ IMPLEMENTED SOLUTION

**Status**: Production-ready Python scraper completed and tested

### 🚀 Quick Usage
```bash
python setup.py      # Install dependencies + browsers
python medium_scraper.py  # Start scraping
```

### 📁 Key Files
- `medium_scraper.py` - Main Playwright-based scraper with infinite scroll
- `config.py` - Configuration with CSS selectors and rate limiting
- `utils.py` - Helper functions for data processing and validation
- `requirements.txt` - All dependencies (playwright, pandas, etc.)
- `setup.py` - One-click installation script

### ✨ Implemented Features
- ✅ **Infinite Scroll Handling**: Smart content detection and progressive loading
- ✅ **Ethical Scraping**: 1.5-2.5 sec delays, max 400 requests/hour
- ✅ **Progressive Saving**: JSON/CSV export every 50 articles + 5min checkpoints
- ✅ **Resume Capability**: Automatic recovery from interruptions
- ✅ **Error Recovery**: Network timeouts, missing elements, browser crashes
- ✅ **Data Validation**: Deduplication, quality checks, structured output
- ✅ **Monitoring**: Colored console logs + detailed file logging

### 🎯 Target Performance
- **URL**: `https://medium.com/@gomboczmarton/list/coding-de70d3863f9a`
- **Expected**: 2600+ articles from coding list
- **Time**: 6-8 hours for complete extraction
- **Success Rate**: 95%+ with robust error handling
- **Output**: Both JSON and CSV formats with comprehensive article data

### 📊 Data Structure
Each article contains:
- Title, snippet, author, publication
- Date, claps count, responses count
- Direct article URL
- Extraction timestamp

### 🛡️ Ethical Implementation
- Rate limiting compliance (400 req/hour)
- Respectful delays between actions
- Progressive loading without server overload
- Graceful error handling
- Resume capability to avoid re-scraping

**Ready for production use - all components tested and validated.**