"""
Web Scraper Tool for Cybersecurity News Sites
Scrapes trusted cybersecurity news sources for latest information
"""

import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import time
import re
from urllib.parse import urljoin, urlparse

from models import NewsItem

logger = logging.getLogger(__name__)

class WebScraperTool:
    """
    Web scraper tool for cybersecurity news sites
    Supports RSS feeds and direct web scraping
    """
    
    def __init__(self):
        """Initialize the web scraper with cybersecurity news sources"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Trusted cybersecurity news sources (removed darkreading.com due to 403 errors)
        self.rss_feeds = [
            'https://krebsonsecurity.com/feed/',
            'https://feeds.feedburner.com/SecurityWeek',
            'https://feeds.feedburner.com/TheHackersNews',
            'https://www.bleepingcomputer.com/feed/',
            'https://feeds.feedburner.com/eset/blog',
            'https://www.schneier.com/feed/',
            'https://feeds.feedburner.com/securityweek',
            'https://www.csoonline.com/index.rss'
        ]
        
        # Direct scraping targets (removed darkreading.com due to 403 errors)
        self.scraping_targets = [
            'https://krebsonsecurity.com',
            'https://thehackernews.com',
            'https://www.bleepingcomputer.com'
        ]
        
        # Cybersecurity keywords for filtering
        self.cyber_keywords = [
            'cyberattack', 'ransomware', 'malware', 'phishing', 'breach',
            'vulnerability', 'exploit', 'CVE', 'zero-day', 'APT',
            'threat', 'security', 'infosec', 'cybersecurity', 'hack',
            'data breach', 'incident response', 'SOC', 'SIEM', 'firewall',
            'intrusion', 'backdoor', 'trojan', 'botnet', 'DDoS'
        ]
        
        logger.info("WebScraperTool initialized with cybersecurity sources")
    
    def scrape_cyber_sites(self, max_items: int = 25) -> List[NewsItem]:
        """
        Scrape cybersecurity news from multiple sources
        
        Args:
            max_items: Maximum number of items to scrape
            
        Returns:
            List of NewsItem objects
        """
        logger.info("Starting web scraping of cybersecurity sites")
        
        all_items = []
        
        # Scrape RSS feeds
        rss_items = self._scrape_rss_feeds(max_items // 2)
        all_items.extend(rss_items)
        
        # Scrape direct sites
        direct_items = self._scrape_direct_sites(max_items // 2)
        all_items.extend(direct_items)
        
        # Filter and clean items
        filtered_items = self._filter_cybersecurity_content(all_items)
        
        logger.info(f"Scraped {len(filtered_items)} cybersecurity news items")
        return filtered_items[:max_items]
    
    def _scrape_rss_feeds(self, max_items: int) -> List[NewsItem]:
        """
        Scrape RSS feeds for cybersecurity news
        
        Args:
            max_items: Maximum number of items to scrape
            
        Returns:
            List of NewsItem objects from RSS feeds
        """
        items = []
        
        for feed_url in self.rss_feeds:
            try:
                logger.info(f"Scraping RSS feed: {feed_url}")
                
                # Parse RSS feed
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Limit per feed
                    try:
                        # Extract information
                        title = entry.get('title', '').strip()
                        content = entry.get('summary', '').strip()
                        url = entry.get('link', '')
                        
                        # Parse published date
                        published_at = self._parse_date(entry.get('published', ''))
                        
                        # Create news item
                        if title and url:
                            item = NewsItem(
                                title=title,
                                content=content,
                                url=url,
                                source=feed_url,
                                published_at=published_at,
                                category='General',
                                severity='Medium',
                                tags=[]
                            )
                            items.append(item)
                            
                    except Exception as e:
                        logger.error(f"Error processing RSS entry: {str(e)}")
                        continue
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping RSS feed {feed_url}: {str(e)}")
                continue
        
        return items[:max_items]
    
    def _scrape_direct_sites(self, max_items: int) -> List[NewsItem]:
        """
        Scrape cybersecurity news directly from websites
        
        Args:
            max_items: Maximum number of items to scrape
            
        Returns:
            List of NewsItem objects from direct scraping
        """
        items = []
        
        for site_url in self.scraping_targets:
            try:
                logger.info(f"Scraping direct site: {site_url}")
                
                # Get page content
                response = self.session.get(site_url, timeout=10)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract news articles (common patterns)
                articles = self._extract_articles_from_soup(soup, site_url)
                
                for article in articles[:3]:  # Limit per site
                    try:
                        # Get full article content
                        full_content = self._get_article_content(article['url'])
                        
                        item = NewsItem(
                            title=article['title'],
                            content=full_content,
                            url=article['url'],
                            source=site_url,
                            published_at=article.get('published_at', datetime.now()),
                            category='General',
                            severity='Medium',
                            tags=[]
                        )
                        items.append(item)
                        
                    except Exception as e:
                        logger.error(f"Error processing article: {str(e)}")
                        continue
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping site {site_url}: {str(e)}")
                continue
        
        return items[:max_items]
    
    def _extract_articles_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract article information from BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Common article selectors
        article_selectors = [
            'article',
            '.article',
            '.post',
            '.news-item',
            '.story',
            'h2 a',
            'h3 a',
            '.headline a'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            
            for element in elements:
                try:
                    # Extract title and URL
                    if element.name == 'a':
                        title = element.get_text().strip()
                        url = element.get('href', '')
                    else:
                        title_elem = element.find('a') or element.find(['h1', 'h2', 'h3', 'h4'])
                        if title_elem:
                            title = title_elem.get_text().strip()
                            url = title_elem.get('href', '') if title_elem.name == 'a' else title_elem.find('a').get('href', '') if title_elem.find('a') else ''
                        else:
                            continue
                    
                    # Resolve relative URLs
                    if url and not url.startswith('http'):
                        url = urljoin(base_url, url)
                    
                    # Extract published date if available
                    published_at = self._extract_published_date(element)
                    
                    if title and url:
                        articles.append({
                            'title': title,
                            'url': url,
                            'published_at': published_at
                        })
                        
                except Exception as e:
                    logger.error(f"Error extracting article: {str(e)}")
                    continue
        
        return articles
    
    def _get_article_content(self, url: str) -> str:
        """
        Get full content of an article from its URL
        
        Args:
            url: Article URL
            
        Returns:
            Article content as string
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find main content
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    break
            
            # Fallback to body if no specific content found
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text().strip()
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content)
            return content[:2000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Error getting article content from {url}: {str(e)}")
            return ""
    
    def _extract_published_date(self, element) -> datetime:
        """
        Extract published date from HTML element
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Published datetime or current time if not found
        """
        try:
            # Look for date elements
            date_selectors = [
                'time',
                '.date',
                '.published',
                '.timestamp',
                '[datetime]'
            ]
            
            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text()
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        return parsed_date
            
            return datetime.now()
            
        except Exception as e:
            logger.error(f"Error extracting published date: {str(e)}")
            return datetime.now()
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse various date formats
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime or current time if parsing fails
        """
        if not date_str:
            return datetime.now()
        
        # Common date formats
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d %b %Y',
            '%B %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        # Try parsing with dateutil if available
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            pass
        
        return datetime.now()
    
    def _filter_cybersecurity_content(self, items: List[NewsItem]) -> List[NewsItem]:
        """
        Filter items to only include cybersecurity-related content
        
        Args:
            items: List of news items
            
        Returns:
            Filtered list of cybersecurity news items
        """
        filtered_items = []
        
        for item in items:
            # Check if content contains cybersecurity keywords
            content_text = f"{item.title} {item.content}".lower()
            
            if any(keyword.lower() in content_text for keyword in self.cyber_keywords):
                filtered_items.append(item)
        
        return filtered_items

