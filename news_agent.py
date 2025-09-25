"""
AI Cybersecurity News & Intelligence Agent
Main agent class that orchestrates multiple tools for news collection and analysis
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from models import NewsItem
from tools.web_scraper import WebScraperTool
from tools.news_api import NewsAPITool
from tools.reddit_api import RedditAPITool
from tools.summarizer import SummarizerTool
from tools.report_generator import ReportGeneratorTool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CyberNewsAgent:
    """
    Main AI Agent for Cybersecurity News & Intelligence
    Orchestrates multiple tools to collect, analyze, and categorize cybersecurity news
    """
    
    def __init__(self):
        """Initialize the agent with all required tools"""
        self.web_scraper = WebScraperTool()
        self.news_api = NewsAPITool()
        self.reddit_api = RedditAPITool()
        self.summarizer = SummarizerTool()
        self.report_generator = ReportGeneratorTool()
        
        # Cybersecurity keywords for filtering
        self.cyber_keywords = [
            'cyberattack', 'ransomware', 'malware', 'phishing', 'breach',
            'vulnerability', 'exploit', 'CVE', 'zero-day', 'APT',
            'threat', 'security', 'infosec', 'cybersecurity', 'hack',
            'data breach', 'incident response', 'SOC', 'SIEM'
        ]
        
        logger.info("CyberNewsAgent initialized successfully")
    
    def collect_news(self, max_items: int = 50) -> List[NewsItem]:
        """
        Collect news from all sources and merge/deduplicate
        
        Args:
            max_items: Maximum number of news items to collect
            
        Returns:
            List of deduplicated NewsItem objects
        """
        logger.info("Starting news collection process")
        
        all_news = []
        
        try:
            # Collect from News API
            logger.info("Collecting from News API")
            news_api_items = self.news_api.fetch_cybersecurity_news(max_items // 3)
            all_news.extend(news_api_items)
            
            # Collect from web scraping
            logger.info("Collecting from web scraping")
            scraped_items = self.web_scraper.scrape_cyber_sites(max_items // 3)
            all_news.extend(scraped_items)
            
            # Collect from Reddit
            logger.info("Collecting from Reddit")
            reddit_items = self.reddit_api.fetch_cybersecurity_posts(max_items // 3)
            all_news.extend(reddit_items)
            
            # Deduplicate based on title similarity
            deduplicated_news = self._deduplicate_news(all_news)
            
            logger.info(f"Collected {len(deduplicated_news)} unique news items")
            return deduplicated_news[:max_items]
            
        except Exception as e:
            logger.error(f"Error collecting news: {str(e)}")
            return []
    
    def analyze_and_categorize(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Analyze news items using AI and categorize them
        
        Args:
            news_items: List of news items to analyze
            
        Returns:
            List of analyzed and categorized news items
        """
        logger.info("Starting AI analysis and categorization")
        
        analyzed_items = []
        
        for item in news_items:
            try:
                # Generate summary and extract key information
                analysis = self.summarizer.analyze_news_item(item)
                
                # Update item with analysis results
                item.summary = analysis.get('summary', '')
                item.category = analysis.get('category', 'General')
                item.severity = analysis.get('severity', 'Medium')
                item.tags = analysis.get('tags', [])
                
                analyzed_items.append(item)
                
            except Exception as e:
                logger.error(f"Error analyzing item '{item.title}': {str(e)}")
                # Keep original item if analysis fails
                analyzed_items.append(item)
        
        logger.info(f"Analyzed {len(analyzed_items)} news items")
        return analyzed_items
    
    def generate_daily_digest(self, news_items: List[NewsItem]) -> str:
        """
        Generate a daily digest summary of all news items
        
        Args:
            news_items: List of analyzed news items
            
        Returns:
            String containing the daily digest
        """
        logger.info("Generating daily digest")
        
        try:
            digest = self.report_generator.generate_daily_digest(news_items)
            logger.info("Daily digest generated successfully")
            return digest
        except Exception as e:
            logger.error(f"Error generating daily digest: {str(e)}")
            return "Unable to generate daily digest at this time."
    
    def search_news(self, query: str, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Search news items by query
        
        Args:
            query: Search query
            news_items: List of news items to search through
            
        Returns:
            List of matching news items
        """
        logger.info(f"Searching news for query: {query}")
        
        query_lower = query.lower()
        matching_items = []
        
        for item in news_items:
            # Search in title, content, and tags
            if (query_lower in item.title.lower() or 
                query_lower in item.content.lower() or 
                any(query_lower in tag.lower() for tag in item.tags)):
                matching_items.append(item)
        
        logger.info(f"Found {len(matching_items)} matching items")
        return matching_items
    
    def get_categorized_news(self, news_items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
        """
        Categorize news items by category
        
        Args:
            news_items: List of news items
            
        Returns:
            Dictionary with categories as keys and lists of items as values
        """
        categorized = {
            'Latest Attacks': [],
            'New Tools': [],
            'Threat Intelligence': [],
            'Vulnerabilities': [],
            'General': []
        }
        
        for item in news_items:
            category = item.category
            if category in categorized:
                categorized[category].append(item)
            else:
                categorized['General'].append(item)
        
        return categorized
    
    def get_severity_stats(self, news_items: List[NewsItem]) -> Dict[str, int]:
        """
        Get severity statistics for news items
        
        Args:
            news_items: List of news items
            
        Returns:
            Dictionary with severity counts
        """
        stats = {'High': 0, 'Medium': 0, 'Low': 0}
        
        for item in news_items:
            severity = item.severity
            if severity in stats:
                stats[severity] += 1
        
        return stats
    
    def _deduplicate_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Remove duplicate news items based on title similarity
        
        Args:
            news_items: List of news items
            
        Returns:
            List of deduplicated news items
        """
        seen_titles = set()
        deduplicated = []
        
        for item in news_items:
            # Simple deduplication based on title
            title_key = item.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                deduplicated.append(item)
        
        return deduplicated
    
    def run_full_pipeline(self, max_items: int = 50) -> Dict[str, Any]:
        """
        Run the complete news collection and analysis pipeline
        
        Args:
            max_items: Maximum number of news items to process
            
        Returns:
            Dictionary containing all processed data
        """
        logger.info("Starting full pipeline execution")
        
        # Step 1: Collect news
        news_items = self.collect_news(max_items)
        
        # Step 2: Analyze and categorize
        analyzed_items = self.analyze_and_categorize(news_items)
        
        # Step 3: Generate daily digest
        daily_digest = self.generate_daily_digest(analyzed_items)
        
        # Step 4: Categorize for frontend
        categorized_news = self.get_categorized_news(analyzed_items)
        
        # Step 5: Get severity statistics
        severity_stats = self.get_severity_stats(analyzed_items)
        
        result = {
            'news_items': analyzed_items,
            'categorized_news': categorized_news,
            'daily_digest': daily_digest,
            'severity_stats': severity_stats,
            'total_items': len(analyzed_items),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Full pipeline execution completed")
        return result

