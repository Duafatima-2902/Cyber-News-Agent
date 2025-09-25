"""
Report Generator Tool for Cybersecurity News Reports
Generates daily digests, PDF reports, and email summaries
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json
from io import BytesIO
import google.generativeai as genai

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from models import NewsItem

logger = logging.getLogger(__name__)

class ReportGeneratorTool:
    """
    Report generator tool for creating cybersecurity news reports
    Supports daily digests, PDF reports, and structured summaries
    """
    
    def __init__(self):
        """Initialize the report generator tool"""
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.use_gemini = True
        else:
            logger.warning("Gemini API key not found, using template-based generation")
            self.use_gemini = False
        
        logger.info("ReportGeneratorTool initialized")
    
    def generate_daily_digest(self, news_items: List[NewsItem]) -> str:
        """
        Generate a daily digest summary of cybersecurity news
        
        Args:
            news_items: List of news items to summarize
            
        Returns:
            Daily digest string
        """
        logger.info("Generating daily digest")
        
        if not news_items:
            return "No cybersecurity news items available for today's digest."
        
        # Skip Gemini API in production to avoid quota issues
        if os.getenv('FLASK_ENV') == 'production':
            logger.info("Production mode: Using template-based digest to avoid API quotas")
            return self._generate_template_digest(news_items)
        
        if self.use_gemini:
            return self._generate_ai_digest(news_items)
        else:
            return self._generate_template_digest(news_items)
    
    def _generate_ai_digest(self, news_items: List[NewsItem]) -> str:
        """
        Generate digest using AI
        
        Args:
            news_items: List of news items
            
        Returns:
            AI-generated digest string
        """
        try:
            # Prepare news data for AI
            news_data = []
            for item in news_items[:10]:  # Limit to avoid token limits
                news_data.append({
                    'title': item.title,
                    'summary': item.summary or item.content[:200],
                    'category': item.category,
                    'severity': item.severity
                })
            
            # Create prompt for AI digest
            prompt = self._create_digest_prompt(news_data)
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.3
                )
            )
            
            digest = response.text.strip()
            logger.info("AI digest generated successfully")
            return digest
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating AI digest: {error_msg}")
            
            # Check if it's a quota exceeded error
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.warning("Gemini API quota exceeded, switching to template-based generation")
                self.use_gemini = False  # Disable Gemini for this session
            
            return self._generate_template_digest(news_items)
    
    def _create_digest_prompt(self, news_data: List[Dict[str, Any]]) -> str:
        """
        Create prompt for AI digest generation
        
        Args:
            news_data: List of news item dictionaries
            
        Returns:
            Prompt string for AI
        """
        news_text = "\n\n".join([
            f"Title: {item['title']}\nSummary: {item['summary']}\nCategory: {item['category']}\nSeverity: {item['severity']}"
            for item in news_data
        ])
        
        return f"""You are a cybersecurity expert creating a daily digest. Write professionally and concisely.

Create a comprehensive daily cybersecurity digest based on the following news items:

{news_text}

Write a professional digest that includes:
1. Executive summary of the day's cybersecurity landscape
2. Key highlights and trends
3. Most critical threats and vulnerabilities
4. Important updates and announcements

Format as a single, well-structured paragraph suitable for executives and security professionals."""
    
    def _generate_template_digest(self, news_items: List[NewsItem]) -> str:
        """
        Generate digest using template-based approach
        
        Args:
            news_items: List of news items
            
        Returns:
            Template-generated digest string
        """
        # Categorize news items
        categorized = self._categorize_news_items(news_items)
        
        # Get severity statistics
        severity_stats = self._get_severity_statistics(news_items)
        
        # Generate digest
        digest_parts = []
        
        # Executive summary
        digest_parts.append(f"Today's cybersecurity landscape shows {len(news_items)} significant developments across multiple threat vectors.")
        
        # High severity items
        high_severity = [item for item in news_items if item.severity == 'High']
        if high_severity:
            digest_parts.append(f"Critical alerts include {len(high_severity)} high-severity incidents, including {high_severity[0].title.lower()}.")
        
        # Category highlights
        for category, items in categorized.items():
            if items:
                digest_parts.append(f"In {category.lower()}, {len(items)} notable developments were reported.")
        
        # Trends
        if severity_stats['High'] > 0:
            digest_parts.append("The threat landscape remains elevated with multiple high-severity incidents requiring immediate attention.")
        elif severity_stats['Medium'] > 0:
            digest_parts.append("Moderate security concerns dominate today's news cycle.")
        else:
            digest_parts.append("Today's security landscape shows relatively low immediate threats.")
        
        return " ".join(digest_parts)
    
    def _categorize_news_items(self, news_items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
        """
        Categorize news items by category
        
        Args:
            news_items: List of news items
            
        Returns:
            Dictionary with categories as keys
        """
        categorized = {}
        
        for item in news_items:
            category = item.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)
        
        return categorized
    
    def _get_severity_statistics(self, news_items: List[NewsItem]) -> Dict[str, int]:
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
    
    def generate_pdf_report(self, news_items: List[NewsItem], title: str = "Cybersecurity News Report") -> BytesIO:
        """
        Generate PDF report from news items
        
        Args:
            news_items: List of news items
            title: Report title
            
        Returns:
            BytesIO object containing PDF data
        """
        logger.info("Generating PDF report")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkred
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive summary
        digest = self.generate_daily_digest(news_items)
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(digest, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Statistics
        severity_stats = self._get_severity_statistics(news_items)
        story.append(Paragraph("Threat Statistics", heading_style))
        
        stats_data = [
            ['Severity Level', 'Count'],
            ['High', str(severity_stats['High'])],
            ['Medium', str(severity_stats['Medium'])],
            ['Low', str(severity_stats['Low'])],
            ['Total', str(len(news_items))]
        ]
        
        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # News items by category
        categorized = self._categorize_news_items(news_items)
        
        for category, items in categorized.items():
            if items:
                story.append(Paragraph(f"{category}", heading_style))
                
                for item in items:
                    # Item title
                    story.append(Paragraph(f"<b>{item.title}</b>", styles['Normal']))
                    
                    # Item details
                    pub_date = item.published_at.replace(tzinfo=None) if item.published_at.tzinfo else item.published_at
                    details = f"<b>Source:</b> {item.source} | <b>Severity:</b> {item.severity} | <b>Published:</b> {pub_date.strftime('%Y-%m-%d %H:%M')}"
                    story.append(Paragraph(details, styles['Normal']))
                    
                    # Summary
                    if item.summary:
                        story.append(Paragraph(item.summary, styles['Normal']))
                    else:
                        story.append(Paragraph(item.content[:300] + "...", styles['Normal']))
                    
                    story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info("PDF report generated successfully")
        return buffer
    
    def generate_email_summary(self, news_items: List[NewsItem]) -> Dict[str, str]:
        """
        Generate professional HTML email summary for news items
        
        Args:
            news_items: List of news items
            
        Returns:
            Dictionary with email subject and body
        """
        logger.info("Generating email summary")
        
        # Generate subject
        severity_stats = self._get_severity_statistics(news_items)
        if severity_stats['High'] > 0:
            subject = f"🚨 URGENT: {severity_stats['High']} Critical Cybersecurity Alerts"
        elif severity_stats['Medium'] > 0:
            subject = f"⚠️ {severity_stats['Medium']} Medium-Severity Security Updates"
        else:
            subject = f"📊 Daily Cybersecurity Digest - {len(news_items)} Updates"
        
        # Generate professional HTML body
        body = self._format_email_html(news_items, severity_stats)
        
        return {
            'subject': subject,
            'body': body
        }
    
    def _format_email_html(self, news_items: List[NewsItem], severity_stats: Dict[str, int]) -> str:
        """
        Format email content as professional HTML
        
        Args:
            news_items: List of news items
            severity_stats: Dictionary with severity counts
            
        Returns:
            HTML formatted email body
        """
        # Get current time for greeting
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good morning"
        elif current_hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        # Get top 5 articles sorted by severity and recency
        top_articles = sorted(news_items, key=lambda x: (
            {'High': 3, 'Medium': 2, 'Low': 1}[x.severity], 
            x.published_at.replace(tzinfo=None) if x.published_at.tzinfo else x.published_at
        ), reverse=True)[:5]
        
        # Generate intro sentence
        total_items = len(news_items)
        high_count = severity_stats['High']
        medium_count = severity_stats['Medium']
        
        if high_count > 0:
            intro = f"We've identified {high_count} critical security alerts that require immediate attention, along with {total_items - high_count} other important updates."
        elif medium_count > 0:
            intro = f"Today's cybersecurity landscape shows {medium_count} medium-severity incidents among {total_items} total security updates."
        else:
            intro = f"Here are today's {total_items} cybersecurity updates and industry developments."
        
        # Build HTML email
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Cybersecurity Digest</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 300;
        }}
        .content {{
            padding: 30px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #2c3e50;
        }}
        .intro {{
            font-size: 16px;
            margin-bottom: 30px;
            color: #555;
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .stats {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .stats h3 {{
            margin-top: 0;
            color: #2c3e50;
            font-size: 18px;
        }}
        .stat-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            display: block;
        }}
        .hot-articles {{
            margin-bottom: 30px;
        }}
        .hot-articles h3 {{
            color: #e74c3c;
            font-size: 20px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 10px;
        }}
        .article {{
            margin-bottom: 25px;
            padding: 15px;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            background-color: #fafbfc;
        }}
        .article-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #2c3e50;
        }}
        .article-title a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        .article-title a:hover {{
            color: #667eea;
            text-decoration: underline;
        }}
        .article-summary {{
            font-size: 14px;
            color: #555;
            margin-bottom: 8px;
            line-height: 1.5;
        }}
        .article-meta {{
            font-size: 12px;
            color: #888;
        }}
        .article-meta .source {{
            font-weight: bold;
            color: #667eea;
        }}
        .article-meta .severity {{
            background-color: #e74c3c;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-left: 10px;
        }}
        .article-meta .severity.medium {{
            background-color: #f39c12;
        }}
        .article-meta .severity.low {{
            background-color: #27ae60;
        }}
        .footer {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 14px;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .timestamp {{
            font-size: 12px;
            color: #95a5a6;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Daily Cybersecurity Digest</h1>
        </div>
        
        <div class="content">
            <div class="greeting">{greeting}, here are today's top cybersecurity updates.</div>
            
            <div class="intro">{intro}</div>
            
            <div class="stats">
                <h3>📊 Today's Security Overview</h3>
                <div class="stat-item">
                    <span class="stat-number">{total_items}</span>
                    <span class="stat-label">Total Updates</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number" style="color: #e74c3c;">{severity_stats['High']}</span>
                    <span class="stat-label">Critical Alerts</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number" style="color: #f39c12;">{severity_stats['Medium']}</span>
                    <span class="stat-label">Medium Priority</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number" style="color: #27ae60;">{severity_stats['Low']}</span>
                    <span class="stat-label">Low Priority</span>
                </div>
            </div>
            
            <div class="hot-articles">
                <h3>🔥 Hot Articles Today</h3>
"""
        
        # Add top articles
        for i, article in enumerate(top_articles, 1):
            # Truncate summary if too long
            summary = article.summary or article.content[:200] + "..." if len(article.content) > 200 else article.content
            
            # Determine severity class
            severity_class = article.severity.lower()
            
            html_body += f"""
                <div class="article">
                    <div class="article-title">
                        <a href="{article.url}" target="_blank">{article.title}</a>
                    </div>
                    <div class="article-summary">{summary}</div>
                    <div class="article-meta">
                        <span class="source">{article.source}</span>
                        <span class="severity {severity_class}">{article.severity}</span>
                    </div>
                </div>
"""
        
        html_body += f"""
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Stay safe and informed.</strong></p>
            <p>— Sent by Cyber News Agent 🤖</p>
            <div class="timestamp">
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        return html_body
    
    def export_to_json(self, news_items: List[NewsItem]) -> str:
        """
        Export news items to JSON format
        
        Args:
            news_items: List of news items
            
        Returns:
            JSON string
        """
        logger.info("Exporting news items to JSON")
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_items': len(news_items),
            'digest': self.generate_daily_digest(news_items),
            'items': []
        }
        
        for item in news_items:
            item_data = {
                'title': item.title,
                'content': item.content,
                'summary': item.summary,
                'url': item.url,
                'source': item.source,
                'published_at': item.published_at.isoformat(),
                'category': item.category,
                'severity': item.severity,
                'tags': item.tags
            }
            export_data['items'].append(item_data)
        
        return json.dumps(export_data, indent=2)

