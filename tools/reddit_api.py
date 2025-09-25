"""
Reddit API Tool for Cybersecurity News
Fetches cybersecurity-related posts from Reddit as an alternative to Twitter
"""

import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import time
import base64

from models import NewsItem

logger = logging.getLogger(__name__)

class RedditAPITool:
    """
    Reddit API tool for fetching cybersecurity news from Reddit
    Uses Reddit's free API to get posts from cybersecurity subreddits
    """
    
    def __init__(self):
        """Initialize the Reddit API tool"""
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = 'CyberNewsAgent/1.0'
        
        # Reddit OAuth endpoint
        self.auth_url = 'https://www.reddit.com/api/v1/access_token'
        self.api_url = 'https://oauth.reddit.com'
        
        # Cybersecurity subreddits
        self.subreddits = [
            'cybersecurity',
            'netsec',
            'security',
            'malware',
            'AskNetsec',
            'ComputerSecurity',
            'cyber',
            'infosec',
            'hacking',
            'privacy'
        ]
        
        # Cybersecurity keywords for filtering
        self.cyber_keywords = [
            'cyberattack', 'ransomware', 'malware', 'phishing', 'breach',
            'vulnerability', 'exploit', 'cve', 'zero-day', 'apt',
            'threat', 'security', 'infosec', 'cybersecurity', 'hack',
            'data breach', 'incident response', 'SOC', 'SIEM', 'firewall',
            'intrusion', 'backdoor', 'trojan', 'botnet', 'DDoS'
        ]
        
        self.access_token = None
        self.token_expires = None
        
        logger.info("RedditAPITool initialized")
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get Reddit OAuth access token
        
        Returns:
            Access token string or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not found")
            return None
        
        try:
            # Prepare credentials
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Prepare headers
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'User-Agent': self.user_agent,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Prepare data
            data = {
                'grant_type': 'client_credentials'
            }
            
            # Make request
            response = requests.post(self.auth_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("Reddit access token obtained successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error getting Reddit access token: {str(e)}")
            return None
    
    def _is_token_valid(self) -> bool:
        """
        Check if current access token is still valid
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token or not self.token_expires:
            return False
        
        return datetime.now() < self.token_expires
    
    def fetch_cybersecurity_posts(self, max_items: int = 25) -> List[NewsItem]:
        """
        Fetch cybersecurity posts from Reddit
        
        Args:
            max_items: Maximum number of posts to fetch
            
        Returns:
            List of NewsItem objects
        """
        logger.info("Fetching cybersecurity posts from Reddit")
        
        if not self._is_token_valid():
            if not self._get_access_token():
                logger.warning("Could not get Reddit access token, using mock data")
                return self._get_mock_posts(max_items)
        
        all_posts = []
        
        try:
            # Fetch from multiple subreddits
            for subreddit in self.subreddits[:5]:  # Limit to avoid rate limits
                try:
                    posts = self._fetch_subreddit_posts(subreddit, max_items // len(self.subreddits[:5]))
                    all_posts.extend(posts)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error fetching from subreddit {subreddit}: {str(e)}")
                    continue
            
            # Filter and deduplicate
            filtered_posts = self._filter_cybersecurity_content(all_posts)
            
            logger.info(f"Fetched {len(filtered_posts)} cybersecurity posts from Reddit")
            return filtered_posts[:max_items]
            
        except Exception as e:
            logger.error(f"Error fetching Reddit posts: {str(e)}")
            return self._get_mock_posts(max_items)
    
    def _fetch_subreddit_posts(self, subreddit: str, max_items: int) -> List[NewsItem]:
        """
        Fetch posts from a specific subreddit
        
        Args:
            subreddit: Subreddit name
            max_items: Maximum number of posts to fetch
            
        Returns:
            List of NewsItem objects
        """
        posts = []
        
        try:
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'User-Agent': self.user_agent
            }
            
            # Fetch hot posts
            url = f"{self.api_url}/r/{subreddit}/hot.json"
            params = {
                'limit': min(25, max_items * 2),  # Get more to filter
                'raw_json': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for post_data in data.get('data', {}).get('children', []):
                try:
                    post = post_data.get('data', {})
                    
                    # Extract post information
                    title = post.get('title', '').strip()
                    content = post.get('selftext', '').strip()
                    url = f"https://reddit.com{post.get('permalink', '')}"
                    author = post.get('author', 'Unknown')
                    
                    # Parse created date
                    created_utc = post.get('created_utc', 0)
                    published_at = datetime.fromtimestamp(created_utc)
                    
                    # Get score and comments count
                    score = post.get('score', 0)
                    num_comments = post.get('num_comments', 0)
                    
                    # Create enhanced content
                    enhanced_content = f"{title}\n\n{content}\n\nScore: {score}, Comments: {num_comments}"
                    
                    if title and len(title) > 10:  # Filter out very short titles
                        item = NewsItem(
                            title=title,
                            content=enhanced_content,
                            url=url,
                            source=f"Reddit r/{subreddit}",
                            published_at=published_at,
                            category='General',
                            severity='Medium',
                            tags=[f'reddit-{subreddit}', f'score-{score}']
                        )
                        posts.append(item)
                        
                except Exception as e:
                    logger.error(f"Error processing Reddit post: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching from subreddit {subreddit}: {str(e)}")
        
        return posts
    
    def _filter_cybersecurity_content(self, posts: List[NewsItem]) -> List[NewsItem]:
        """
        Filter posts to only include cybersecurity-related content
        
        Args:
            posts: List of posts
            
        Returns:
            Filtered list of cybersecurity posts
        """
        filtered_posts = []
        seen_titles = set()
        
        for post in posts:
            # Deduplicate based on title
            title_key = post.title.lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            # Check if content contains cybersecurity keywords
            content_text = f"{post.title} {post.content}".lower()
            
            if any(keyword.lower() in content_text for keyword in self.cyber_keywords):
                filtered_posts.append(post)
        
        return filtered_posts
    
    def _get_mock_posts(self, max_items: int) -> List[NewsItem]:
        """
        Generate mock Reddit posts for testing
        
        Args:
            max_items: Number of mock posts to generate
            
        Returns:
            List of mock NewsItem objects
        """
        mock_posts = [
            {
                'title': 'New Ransomware Campaign Targeting Healthcare Organizations',
                'content': 'Security researchers have identified a new ransomware variant specifically targeting healthcare systems. The malware uses sophisticated encryption and demands payment in cryptocurrency.',
                'source': 'Reddit r/cybersecurity',
                'category': 'Latest Attacks',
                'severity': 'High'
            },
            {
                'title': 'Zero-Day Vulnerability Found in Popular VPN Software',
                'content': 'A critical zero-day vulnerability has been discovered in a widely-used VPN application that could allow remote code execution.',
                'source': 'Reddit r/netsec',
                'category': 'Vulnerabilities',
                'severity': 'High'
            },
            {
                'title': 'Open Source SIEM Tool Released for Small Businesses',
                'content': 'A new open-source Security Information and Event Management (SIEM) solution has been released, designed specifically for small and medium businesses.',
                'source': 'Reddit r/security',
                'category': 'New Tools',
                'severity': 'Low'
            },
            {
                'title': 'Phishing Campaign Uses AI-Generated Voice Messages',
                'content': 'Security researchers report a new phishing campaign that uses AI-generated voice messages to trick victims into revealing sensitive information.',
                'source': 'Reddit r/malware',
                'category': 'Threat Intelligence',
                'severity': 'Medium'
            },
            {
                'title': 'GDPR Compliance Checklist for Small Businesses',
                'content': 'A comprehensive guide to help small businesses understand and implement GDPR compliance requirements.',
                'source': 'Reddit r/privacy',
                'category': 'General',
                'severity': 'Low'
            }
        ]
        
        posts = []
        for i, mock_data in enumerate(mock_posts[:max_items]):
            post = NewsItem(
                title=mock_data['title'],
                content=mock_data['content'],
                url=f"https://reddit.com/r/cybersecurity/comments/mock{i+1}",
                source=mock_data['source'],
                published_at=datetime.now() - timedelta(hours=i),
                category=mock_data['category'],
                severity=mock_data['severity'],
                tags=['reddit', 'mock', 'cybersecurity']
            )
            posts.append(post)
        
        return posts
