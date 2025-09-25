"""
News API Tool for structured cybersecurity news
Integrates with NewsAPI.org and other news APIs for structured data
"""

import requests
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from models import NewsItem

logger = logging.getLogger(__name__)

class NewsAPITool:
    """
    News API tool for fetching structured cybersecurity news
    Supports multiple news APIs including NewsAPI.org
    """
    
    def __init__(self):
        """Initialize the News API tool"""
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.session = requests.Session()
        
        # NewsAPI.org endpoints
        self.newsapi_base_url = 'https://newsapi.org/v2'
        
        # Cybersecurity keywords for filtering
        self.cyber_keywords = [
            'cybersecurity', 'cyber attack', 'ransomware', 'malware', 'phishing',
            'data breach', 'vulnerability', 'exploit', 'CVE', 'zero-day',
            'threat', 'security', 'infosec', 'hack', 'hacker', 'APT',
            'incident response', 'SOC', 'SIEM', 'firewall', 'intrusion'
        ]
        
        # Trusted cybersecurity news sources
        self.trusted_sources = [
            'krebsonsecurity', 'dark-reading', 'securityweek', 'bleepingcomputer',
            'the-hacker-news', 'cso-online', 'infosecurity-magazine', 'threatpost',
            'cyberscoop', 'security-boulevard', 'helpnetsecurity', 'tripwire'
        ]
        
        logger.info("NewsAPITool initialized")
    
    def fetch_cybersecurity_news(self, max_items: int = 25) -> List[NewsItem]:
        """
        Fetch cybersecurity news from NewsAPI.org
        
        Args:
            max_items: Maximum number of items to fetch
            
        Returns:
            List of NewsItem objects
        """
        logger.info("Fetching cybersecurity news from NewsAPI")
        
        all_items = []
        
        # Skip News API in production to avoid rate limits
        if os.getenv('FLASK_ENV') == 'production':
            logger.info("Production mode: Skipping News API to avoid rate limits")
            return []
        
        if not self.news_api_key:
            logger.warning("NewsAPI key not found, using mock data")
            return self._get_mock_news_items(max_items)
        
        try:
            # Fetch from multiple endpoints
            endpoints = [
                self._fetch_everything_endpoint,
                self._fetch_top_headlines_endpoint,
                self._fetch_sources_endpoint
            ]
            
            for endpoint_func in endpoints:
                try:
                    items = endpoint_func(max_items // len(endpoints))
                    all_items.extend(items)
                except Exception as e:
                    logger.error(f"Error fetching from endpoint: {str(e)}")
                    continue
            
            # Filter and deduplicate
            filtered_items = self._filter_cybersecurity_content(all_items)
            
            logger.info(f"Fetched {len(filtered_items)} cybersecurity news items")
            return filtered_items[:max_items]
            
        except Exception as e:
            logger.error(f"Error fetching news from NewsAPI: {str(e)}")
            return self._get_mock_news_items(max_items)
    
    def _fetch_everything_endpoint(self, max_items: int) -> List[NewsItem]:
        """
        Fetch news from NewsAPI everything endpoint
        
        Args:
            max_items: Maximum number of items to fetch
            
        Returns:
            List of NewsItem objects
        """
        items = []
        
        # Search for cybersecurity-related terms (reduced to avoid rate limits)
        for keyword in self.cyber_keywords[:2]:  # Only 2 keywords to avoid rate limits
            try:
                url = f"{self.newsapi_base_url}/everything"
                params = {
                    'q': keyword,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': min(20, max_items),
                    'apiKey': self.news_api_key
                }
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') == 'ok':
                    for article in data.get('articles', []):
                        item = self._parse_newsapi_article(article)
                        if item:
                            items.append(item)
                
                # Rate limiting - increased delay to avoid 429 errors
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error fetching everything for keyword '{keyword}': {str(e)}")
                continue
        
        return items
    
    def _fetch_top_headlines_endpoint(self, max_items: int) -> List[NewsItem]:
        """
        Fetch top headlines from NewsAPI
        
        Args:
            max_items: Maximum number of items to fetch
            
        Returns:
            List of NewsItem objects
        """
        items = []
        
        try:
            url = f"{self.newsapi_base_url}/top-headlines"
            params = {
                'category': 'technology',
                'language': 'en',
                'pageSize': min(20, max_items),
                'apiKey': self.news_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                for article in data.get('articles', []):
                    item = self._parse_newsapi_article(article)
                    if item and self._is_cybersecurity_related(item):
                        items.append(item)
            
        except Exception as e:
            logger.error(f"Error fetching top headlines: {str(e)}")
        
        return items
    
    def _fetch_sources_endpoint(self, max_items: int) -> List[NewsItem]:
        """
        Fetch news from specific cybersecurity sources
        
        Args:
            max_items: Maximum number of items to fetch
            
        Returns:
            List of NewsItem objects
        """
        items = []
        
        # Get available sources first
        try:
            url = f"{self.newsapi_base_url}/sources"
            params = {
                'category': 'technology',
                'language': 'en',
                'apiKey': self.news_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                sources = data.get('sources', [])
                
                # Filter for cybersecurity sources
                cyber_sources = [
                    source['id'] for source in sources 
                    if any(keyword in source.get('name', '').lower() 
                          for keyword in ['security', 'cyber', 'tech', 'computer'])
                ]
                
                # Fetch news from cybersecurity sources
                for source_id in cyber_sources[:3]:  # Limit to avoid rate limits
                    try:
                        url = f"{self.newsapi_base_url}/everything"
                        params = {
                            'sources': source_id,
                            'language': 'en',
                            'sortBy': 'publishedAt',
                            'pageSize': min(10, max_items),
                            'apiKey': self.news_api_key
                        }
                        
                        response = self.session.get(url, params=params, timeout=10)
                        response.raise_for_status()
                        
                        data = response.json()
                        
                        if data.get('status') == 'ok':
                            for article in data.get('articles', []):
                                item = self._parse_newsapi_article(article)
                                if item and self._is_cybersecurity_related(item):
                                    items.append(item)
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error fetching from source {source_id}: {str(e)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error fetching sources: {str(e)}")
        
        return items
    
    def _parse_newsapi_article(self, article: Dict[str, Any]) -> Optional[NewsItem]:
        """
        Parse NewsAPI article into NewsItem
        
        Args:
            article: NewsAPI article dictionary
            
        Returns:
            NewsItem object or None if parsing fails
        """
        try:
            title = article.get('title', '').strip()
            content = article.get('description', '').strip()
            url = article.get('url', '')
            source = article.get('source', {}).get('name', 'Unknown')
            
            # Parse published date
            published_str = article.get('publishedAt', '')
            published_at = self._parse_newsapi_date(published_str)
            
            if title and url:
                return NewsItem(
                    title=title,
                    content=content,
                    url=url,
                    source=source,
                    published_at=published_at,
                    category='General',
                    severity='Medium',
                    tags=[]
                )
        
        except Exception as e:
            logger.error(f"Error parsing NewsAPI article: {str(e)}")
        
        return None
    
    def _parse_newsapi_date(self, date_str: str) -> datetime:
        """
        Parse NewsAPI date format
        
        Args:
            date_str: Date string from NewsAPI
            
        Returns:
            Parsed datetime or current time if parsing fails
        """
        try:
            # NewsAPI uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.error(f"Error parsing NewsAPI date '{date_str}': {str(e)}")
            return datetime.now()
    
    def _is_cybersecurity_related(self, item: NewsItem) -> bool:
        """
        Check if a news item is cybersecurity-related
        
        Args:
            item: NewsItem to check
            
        Returns:
            True if cybersecurity-related, False otherwise
        """
        content_text = f"{item.title} {item.content}".lower()
        return any(keyword.lower() in content_text for keyword in self.cyber_keywords)
    
    def _filter_cybersecurity_content(self, items: List[NewsItem]) -> List[NewsItem]:
        """
        Filter items to only include cybersecurity-related content
        
        Args:
            items: List of news items
            
        Returns:
            Filtered list of cybersecurity news items
        """
        filtered_items = []
        seen_titles = set()
        
        for item in items:
            # Deduplicate and filter
            title_key = item.title.lower().strip()
            if title_key not in seen_titles and self._is_cybersecurity_related(item):
                seen_titles.add(title_key)
                filtered_items.append(item)
        
        return filtered_items
    
    def _get_mock_news_items(self, max_items: int) -> List[NewsItem]:
        """
        Generate mock cybersecurity news items for testing
        
        Args:
            max_items: Number of mock items to generate
            
        Returns:
            List of mock NewsItem objects
        """
        mock_items = [
            {
                'title': 'Major Ransomware Attack Targets Healthcare Sector',
                'content': 'A sophisticated ransomware attack has targeted multiple healthcare facilities across the country, causing significant disruption to patient care services.',
                'source': 'SecurityWeek',
                'category': 'Latest Attacks',
                'severity': 'High'
            },
            {
                'title': 'New Zero-Day Vulnerability Discovered in Popular Software',
                'content': 'Security researchers have identified a critical zero-day vulnerability that could allow remote code execution in widely-used enterprise software.',
                'source': 'Dark Reading',
                'category': 'Vulnerabilities',
                'severity': 'High'
            },
            {
                'title': 'AI-Powered Threat Detection Tool Released',
                'content': 'A new AI-powered threat detection platform has been launched, promising to revolutionize how organizations identify and respond to cyber threats.',
                'source': 'CSO Online',
                'category': 'New Tools',
                'severity': 'Low'
            },
            {
                'title': 'Phishing Campaign Targets Remote Workers',
                'content': 'A sophisticated phishing campaign is targeting remote workers with fake collaboration tool notifications, attempting to steal credentials.',
                'source': 'Threatpost',
                'category': 'Threat Intelligence',
                'severity': 'Medium'
            },
            {
                'title': 'New Cybersecurity Framework Released by NIST',
                'content': 'The National Institute of Standards and Technology has released an updated cybersecurity framework with enhanced guidance for organizations.',
                'source': 'Infosecurity Magazine',
                'category': 'General',
                'severity': 'Low'
            }
        ]
        
        items = []
        for i, mock_data in enumerate(mock_items[:max_items]):
            item = NewsItem(
                title=mock_data['title'],
                content=mock_data['content'],
                url=f"https://example.com/news/{i+1}",
                source=mock_data['source'],
                published_at=datetime.now() - timedelta(hours=i),
                category=mock_data['category'],
                severity=mock_data['severity'],
                tags=['mock', 'cybersecurity']
            )
            items.append(item)
        
        return items

