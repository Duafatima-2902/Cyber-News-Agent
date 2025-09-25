"""
AI Summarizer Tool for Cybersecurity News Analysis
Uses Google Gemini API to analyze, summarize, and categorize news items
"""

import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
import json
import re
from datetime import datetime

from models import NewsItem

logger = logging.getLogger(__name__)

class SummarizerTool:
    """
    AI-powered summarizer tool for cybersecurity news analysis
    Uses Google Gemini models for intelligent content analysis
    """
    
    def __init__(self):
        """Initialize the summarizer tool"""
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.use_gemini = True
        else:
            logger.warning("Gemini API key not found, using rule-based analysis")
            self.use_gemini = False
        
        # Cybersecurity categories
        self.categories = {
            'Latest Attacks': ['ransomware', 'malware', 'attack', 'breach', 'hack', 'incident'],
            'Vulnerabilities': ['vulnerability', 'exploit', 'cve', 'zero-day', 'patch', 'flaw'],
            'New Tools': ['tool', 'platform', 'software', 'solution', 'framework', 'technology'],
            'Threat Intelligence': ['threat', 'intelligence', 'apt', 'campaign', 'actor', 'group'],
            'General': ['security', 'cybersecurity', 'infosec', 'policy', 'regulation', 'compliance']
        }
        
        # Severity keywords
        self.severity_keywords = {
            'High': ['critical', 'severe', 'urgent', 'emergency', 'zero-day', 'ransomware', 'breach'],
            'Medium': ['moderate', 'significant', 'important', 'vulnerability', 'exploit'],
            'Low': ['minor', 'update', 'patch', 'tool', 'announcement', 'guidance']
        }
        
        logger.info("SummarizerTool initialized")
    
    def analyze_news_item(self, item: NewsItem) -> Dict[str, Any]:
        """
        Analyze a news item using AI or rule-based methods
        
        Args:
            item: NewsItem to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # Skip Gemini API in production to avoid quota issues
        if os.getenv('FLASK_ENV') == 'production':
            logger.info("Production mode: Using rule-based analysis to avoid API quotas")
            return self._analyze_with_rules(item)
        
        if self.use_gemini:
            return self._analyze_with_gemini(item)
        else:
            return self._analyze_with_rules(item)
    
    def _analyze_with_gemini(self, item: NewsItem) -> Dict[str, Any]:
        """
        Analyze news item using Gemini API
        
        Args:
            item: NewsItem to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Prepare content for analysis
            content = f"Title: {item.title}\n\nContent: {item.content}"
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(content)
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3
                )
            )
            
            # Parse response
            analysis_text = response.text.strip()
            return self._parse_gemini_response(analysis_text)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error analyzing with Gemini: {error_msg}")
            
            # Check if it's a quota exceeded error
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.warning("Gemini API quota exceeded, switching to rule-based analysis")
                self.use_gemini = False  # Disable Gemini for this session
            
            return self._analyze_with_rules(item)
    
    def _create_analysis_prompt(self, content: str) -> str:
        """
        Create analysis prompt for Gemini
        
        Args:
            content: News content to analyze
            
        Returns:
            Analysis prompt string
        """
        return f"""You are a cybersecurity expert analyzing news articles. Provide accurate, concise analysis.

Analyze this cybersecurity news article and provide:

1. A concise 2-3 sentence summary
2. Category (Latest Attacks, Vulnerabilities, New Tools, Threat Intelligence, or General)
3. Severity level (High, Medium, or Low)
4. Key tags/keywords (3-5 relevant terms)

Article:
{content}

Respond in JSON format:
{{
    "summary": "Brief summary here",
    "category": "Category name",
    "severity": "High/Medium/Low",
    "tags": ["tag1", "tag2", "tag3"]
}}"""
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response into structured data
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed analysis dictionary
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                return {
                    'summary': analysis.get('summary', ''),
                    'category': analysis.get('category', 'General'),
                    'severity': analysis.get('severity', 'Medium'),
                    'tags': analysis.get('tags', [])
                }
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
        
        # Fallback to rule-based analysis
        return self._analyze_with_rules_from_text(response_text)
    
    def _analyze_with_rules(self, item: NewsItem) -> Dict[str, Any]:
        """
        Analyze news item using rule-based methods
        
        Args:
            item: NewsItem to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        content_text = f"{item.title} {item.content}".lower()
        
        # Generate summary
        summary = self._generate_rule_based_summary(item)
        
        # Determine category
        category = self._determine_category(content_text)
        
        # Determine severity
        severity = self._determine_severity(content_text)
        
        # Extract tags
        tags = self._extract_tags(content_text)
        
        return {
            'summary': summary,
            'category': category,
            'severity': severity,
            'tags': tags
        }
    
    def _analyze_with_rules_from_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text using rule-based methods (fallback)
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        content_text = text.lower()
        
        return {
            'summary': text[:200] + "..." if len(text) > 200 else text,
            'category': self._determine_category(content_text),
            'severity': self._determine_severity(content_text),
            'tags': self._extract_tags(content_text)
        }
    
    def _generate_rule_based_summary(self, item: NewsItem) -> str:
        """
        Generate summary using rule-based methods
        
        Args:
            item: NewsItem to summarize
            
        Returns:
            Generated summary string
        """
        # Simple extractive summarization
        sentences = item.content.split('. ')
        if len(sentences) > 1:
            # Take first sentence and one with most cybersecurity keywords
            summary_sentences = [sentences[0]]
            
            # Find sentence with most cybersecurity keywords
            cyber_keywords = ['attack', 'breach', 'vulnerability', 'threat', 'security', 'malware', 'ransomware']
            best_sentence = ""
            max_keywords = 0
            
            for sentence in sentences[1:]:
                keyword_count = sum(1 for keyword in cyber_keywords if keyword in sentence.lower())
                if keyword_count > max_keywords:
                    max_keywords = keyword_count
                    best_sentence = sentence
            
            if best_sentence and best_sentence != sentences[0]:
                summary_sentences.append(best_sentence)
            
            return '. '.join(summary_sentences) + '.'
        else:
            return item.content[:200] + "..." if len(item.content) > 200 else item.content
    
    def _determine_category(self, content_text: str) -> str:
        """
        Determine category based on content keywords
        
        Args:
            content_text: Lowercase content text
            
        Returns:
            Determined category
        """
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in content_text)
            category_scores[category] = score
        
        # Return category with highest score, default to General
        best_category = max(category_scores, key=category_scores.get)
        return best_category if category_scores[best_category] > 0 else 'General'
    
    def _determine_severity(self, content_text: str) -> str:
        """
        Determine severity based on content keywords
        
        Args:
            content_text: Lowercase content text
            
        Returns:
            Determined severity level
        """
        severity_scores = {}
        
        for severity, keywords in self.severity_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_text)
            severity_scores[severity] = score
        
        # Return severity with highest score, default to Medium
        best_severity = max(severity_scores, key=severity_scores.get)
        return best_severity if severity_scores[best_severity] > 0 else 'Medium'
    
    def _extract_tags(self, content_text: str) -> List[str]:
        """
        Extract relevant tags from content
        
        Args:
            content_text: Lowercase content text
            
        Returns:
            List of extracted tags
        """
        # Common cybersecurity tags
        all_tags = [
            'ransomware', 'malware', 'phishing', 'breach', 'vulnerability',
            'exploit', 'cve', 'zero-day', 'apt', 'threat', 'security',
            'cybersecurity', 'infosec', 'hack', 'attack', 'incident',
            'tool', 'platform', 'framework', 'policy', 'compliance'
        ]
        
        # Find tags present in content
        found_tags = [tag for tag in all_tags if tag in content_text]
        
        # Limit to 5 tags
        return found_tags[:5]
    
    def batch_analyze(self, items: List[NewsItem]) -> List[NewsItem]:
        """
        Analyze multiple news items in batch
        
        Args:
            items: List of NewsItem objects
            
        Returns:
            List of analyzed NewsItem objects
        """
        logger.info(f"Batch analyzing {len(items)} news items")
        
        analyzed_items = []
        
        for item in items:
            try:
                analysis = self.analyze_news_item(item)
                
                # Update item with analysis results
                item.summary = analysis.get('summary', '')
                item.category = analysis.get('category', 'General')
                item.severity = analysis.get('severity', 'Medium')
                item.tags = analysis.get('tags', [])
                
                analyzed_items.append(item)
                
            except Exception as e:
                logger.error(f"Error analyzing item '{item.title}': {str(e)}")
                analyzed_items.append(item)
        
        logger.info(f"Batch analysis completed for {len(analyzed_items)} items")
        return analyzed_items

