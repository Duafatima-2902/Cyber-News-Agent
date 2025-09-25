"""
Notification Service for CyberNewsAgent
Handles daily notifications via email, webhooks, and scheduled tasks
"""

import os
import smtplib
import requests
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from models import NewsItem
from tools.report_generator import ReportGeneratorTool

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending daily cybersecurity news notifications
    Supports email, webhook, and scheduled delivery
    """
    
    def __init__(self):
        """Initialize the notification service"""
        self.report_generator = ReportGeneratorTool()
        self.email_config = self._load_email_config()
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.notification_time = os.getenv('NOTIFICATION_TIME', '09:00')  # Default 9:00 AM
        self.is_running = False
        self.subscribers_file = 'subscribers.txt'
        self.subscribers = self._load_subscribers()
        
        # Auto-start scheduler if there are subscribers and email is configured
        logger.info(f"Auto-start check - Subscribers: {len(self.subscribers)}, Email configured: {bool(self.email_config['email'])}, Password configured: {bool(self.email_config['password'])}")
        if self.subscribers and self.email_config['email'] and self.email_config['password']:
            self.start_daily_scheduler()
            logger.info("Auto-started daily scheduler due to existing subscribers")
        else:
            logger.info("Auto-start skipped - missing subscribers or email configuration")
        
        logger.info("NotificationService initialized")
    
    def _load_email_config(self) -> Dict[str, str]:
        """Load email configuration from environment variables"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('NOTIFICATION_EMAIL'),
            'password': os.getenv('EMAIL_PASSWORD')
        }
    
    def _load_subscribers(self) -> set:
        """Load subscriber emails from file"""
        try:
            if os.path.exists(self.subscribers_file):
                with open(self.subscribers_file, 'r') as f:
                    subscribers = set(line.strip().lower() for line in f if line.strip())
                logger.info(f"Loaded {len(subscribers)} subscribers")
                return subscribers
            else:
                logger.info("No subscribers file found, starting with empty list")
                return set()
        except Exception as e:
            logger.error(f"Error loading subscribers: {str(e)}")
            return set()
    
    def _save_subscribers(self):
        """Save subscriber emails to file"""
        try:
            with open(self.subscribers_file, 'w') as f:
                for email in sorted(self.subscribers):
                    f.write(f"{email}\n")
            logger.info(f"Saved {len(self.subscribers)} subscribers")
        except Exception as e:
            logger.error(f"Error saving subscribers: {str(e)}")
    
    def add_subscriber(self, email: str) -> bool:
        """Add a new subscriber"""
        email = email.strip().lower()
        if email in self.subscribers:
            logger.info(f"Email {email} already subscribed")
            return False
        
        self.subscribers.add(email)
        self._save_subscribers()
        logger.info(f"Added new subscriber: {email}")
        
        # Check email configuration before sending welcome email
        logger.info(f"Email config check - Email: {bool(self.email_config['email'])}, Password: {bool(self.email_config['password'])}")
        
        # Send welcome email
        try:
            logger.info(f"Attempting to send welcome email to: {email}")
            success = self.send_welcome_email(email)
            if success:
                logger.info(f"Welcome email sent successfully to: {email}")
            else:
                logger.error(f"Welcome email failed to send to: {email}")
        except Exception as e:
            logger.error(f"Exception sending welcome email to {email}: {str(e)}")
            # Don't fail the subscription if welcome email fails
        
        return True
    
    def remove_subscriber(self, email: str) -> bool:
        """Remove a subscriber"""
        email = email.strip().lower()
        if email in self.subscribers:
            self.subscribers.remove(email)
            self._save_subscribers()
            logger.info(f"Removed subscriber: {email}")
            return True
        return False
    
    def get_subscriber_count(self) -> int:
        """Get total number of subscribers"""
        return len(self.subscribers)
    
    def send_daily_notification(self, news_items: List[NewsItem]) -> bool:
        """
        Send daily notification with cybersecurity news to all subscribers
        
        Args:
            news_items: List of news items to include in notification
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        logger.info(f"Sending daily notification for {len(news_items)} items to {len(self.subscribers)} subscribers")
        
        success = True
        
        # Send email notification to all subscribers
        if self.email_config['email'] and self.email_config['password'] and self.subscribers:
            try:
                self._send_email_notification_to_subscribers(news_items)
                logger.info(f"Email notification sent successfully to {len(self.subscribers)} subscribers")
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
                success = False
        elif not self.subscribers:
            logger.info("No subscribers to send notifications to")
        
        # Send webhook notification
        if self.webhook_url:
            try:
                self._send_webhook_notification(news_items)
                logger.info("Webhook notification sent successfully")
            except Exception as e:
                logger.error(f"Failed to send webhook notification: {str(e)}")
                success = False
        
        return success
    
    def _send_email_notification_to_subscribers(self, news_items: List[NewsItem]):
        """Send email notification to all subscribers"""
        email_data = self.report_generator.generate_email_summary(news_items)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_config['email']
        msg['Subject'] = email_data['subject']
        
        # Add body
        msg.attach(MIMEText(email_data['body'], 'html'))
        
        # Send email to all subscribers
        with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            
            for subscriber_email in self.subscribers:
                try:
                    msg['To'] = subscriber_email
                    server.send_message(msg)
                    logger.info(f"Email sent to subscriber: {subscriber_email}")
                except Exception as e:
                    logger.error(f"Failed to send email to {subscriber_email}: {str(e)}")
    
    def _send_email_notification(self, news_items: List[NewsItem]):
        """Send email notification to admin email (for testing)"""
        email_data = self.report_generator.generate_email_summary(news_items)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_config['email']
        msg['To'] = self.email_config['email']  # Send admin notifications to the notification email
        msg['Subject'] = email_data['subject']
        
        # Add body
        msg.attach(MIMEText(email_data['body'], 'html'))
        
        # Send email
        with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            server.send_message(msg)
    
    def _send_webhook_notification(self, news_items: List[NewsItem]):
        """Send webhook notification (for Discord, Slack, etc.)"""
        severity_stats = self._get_severity_statistics(news_items)
        
        # Create webhook payload
        payload = {
            "content": f"🚨 **Daily Cybersecurity Alert**",
            "embeds": [{
                "title": "CyberNewsAgent Daily Digest",
                "description": f"Found {len(news_items)} cybersecurity updates",
                "color": 0xff0000 if severity_stats['High'] > 0 else 0xffa500,
                "fields": [
                    {
                        "name": "📊 Statistics",
                        "value": f"High: {severity_stats['High']}\nMedium: {severity_stats['Medium']}\nLow: {severity_stats['Low']}",
                        "inline": True
                    },
                    {
                        "name": "🔗 Access Dashboard",
                        "value": f"[Open CyberNewsAgent]({os.getenv('APP_URL', 'http://localhost:5000')})",
                        "inline": True
                    }
                ],
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "CyberNewsAgent"
                }
            }]
        }
        
        # Add top news items
        if news_items:
            top_items = sorted(news_items, key=lambda x: x.severity, reverse=True)[:5]
            items_text = "\n".join([f"• {item.title} ({item.severity})" for item in top_items])
            payload["embeds"][0]["fields"].append({
                "name": "🔥 Top Stories",
                "value": items_text[:1000],  # Discord limit
                "inline": False
            })
        
        # Send webhook
        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()
    
    def _get_severity_statistics(self, news_items: List[NewsItem]) -> Dict[str, int]:
        """Get severity statistics for news items"""
        stats = {'High': 0, 'Medium': 0, 'Low': 0}
        for item in news_items:
            if item.severity in stats:
                stats[item.severity] += 1
        return stats
    
    def start_daily_scheduler(self):
        """Start the daily notification scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        
        # Schedule daily notification
        schedule.every().day.at(self.notification_time).do(self._daily_notification_job)
        
        logger.info(f"Daily notification scheduler started - will send at {self.notification_time}")
        
        # Run scheduler in background thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def stop_daily_scheduler(self):
        """Stop the daily notification scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Daily notification scheduler stopped")
    
    def _daily_notification_job(self):
        """Job to run daily notification"""
        try:
            logger.info("Running daily notification job")
            
            # Import here to avoid circular imports
            from news_agent import CyberNewsAgent
            
            # Collect news
            agent = CyberNewsAgent()
            news_items = agent.collect_news(max_items=20)
            
            # Send notification
            self.send_daily_notification(news_items)
            
        except Exception as e:
            logger.error(f"Daily notification job failed: {str(e)}")
    
    def send_test_notification(self) -> bool:
        """Send a test notification"""
        logger.info("Sending test notification")
        
        # Create test news items
        test_items = [
            NewsItem(
                title="Test Cybersecurity Alert",
                content="This is a test notification from CyberNewsAgent",
                url="https://example.com",
                source="Test Source",
                published_at=datetime.now(),
                category="Test",
                severity="Medium",
                tags=["test", "notification"],
                summary="Test notification to verify email/webhook setup"
            )
        ]
        
        return self.send_daily_notification(test_items)
    
    def send_welcome_email(self, subscriber_email: str) -> bool:
        """Send welcome email to new subscriber"""
        try:
            # Create welcome email content
            welcome_data = self._generate_welcome_email(subscriber_email)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = subscriber_email
            msg['Subject'] = welcome_data['subject']
            
            # Add body
            msg.attach(MIMEText(welcome_data['body'], 'html'))
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['email'], self.email_config['password'])
                server.send_message(msg)
            
            logger.info(f"Welcome email sent to: {subscriber_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {subscriber_email}: {str(e)}")
            return False
    
    def _generate_welcome_email(self, subscriber_email: str) -> Dict[str, str]:
        """Generate welcome email content"""
        current_time = datetime.now()
        
        # Dynamic greeting based on time
        if current_time.hour < 12:
            greeting = "Good morning"
        elif current_time.hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        subject = "🛡️ Welcome to CyberNewsAgent - Let's Dive Into the Cyber World Together!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to CyberNewsAgent</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #00ff88;
                }}
                .header h1 {{
                    color: #00ff88;
                    font-size: 28px;
                    margin: 0;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .welcome-message {{
                    font-size: 18px;
                    margin-bottom: 25px;
                    text-align: center;
                    color: #2c3e50;
                }}
                .features {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .features h3 {{
                    color: #00ff88;
                    margin-top: 0;
                }}
                .feature-item {{
                    margin: 10px 0;
                    padding-left: 20px;
                    position: relative;
                }}
                .feature-item::before {{
                    content: "🛡️";
                    position: absolute;
                    left: 0;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #00ff88, #00cc6a);
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    text-align: center;
                    margin: 20px 0;
                    box-shadow: 0 4px 8px rgba(0, 255, 136, 0.3);
                    transition: transform 0.2s;
                }}
                .cta-button:hover {{
                    transform: translateY(-2px);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 14px;
                }}
                .emoji {{
                    font-size: 24px;
                    margin: 0 5px;
                }}
                .highlight {{
                    background: linear-gradient(120deg, #00ff88 0%, #00cc6a 100%);
                    color: white;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="emoji">🛡️</span> CyberNewsAgent <span class="emoji">🤖</span></h1>
                </div>
                
                <div class="welcome-message">
                    <strong>{greeting}, Cybersecurity Warrior!</strong><br>
                    Welcome to the most exciting cybersecurity community! 🎉
                </div>
                
                <p>You've just joined an elite group of security professionals, researchers, and enthusiasts who stay ahead of the curve. <span class="highlight">Let's dive into the cyber world together!</span></p>
                
                <div class="features">
                    <h3>🚀 What You'll Get:</h3>
                    <div class="feature-item">Daily cybersecurity digest at <strong>9:00 AM</strong></div>
                    <div class="feature-item">Top 5 hottest articles with AI-powered analysis</div>
                    <div class="feature-item">Professional HTML emails with clickable links</div>
                    <div class="feature-item">Severity classifications (High/Medium/Low)</div>
                    <div class="feature-item">Real-time threat intelligence and trends</div>
                    <div class="feature-item">Access to our web dashboard anytime</div>
                </div>
                
                <div style="text-align: center;">
                    <a href="{os.getenv('APP_URL', 'http://localhost:5000')}" class="cta-button">
                        🌐 Explore Dashboard
                    </a>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <strong>🎯 Your First Email:</strong><br>
                    You'll receive your first cybersecurity digest tomorrow at <strong>9:00 AM</strong>. 
                    Get ready for the latest threats, vulnerabilities, and security insights!
                </div>
                
                <p><strong>Pro Tip:</strong> Add our email to your contacts to ensure you never miss a critical security update!</p>
                
                <div class="footer">
                    <p><strong>Stay Safe, Stay Informed!</strong></p>
                    <p>— Your CyberNewsAgent Team <span class="emoji">🤖</span></p>
                    <p style="font-size: 12px; color: #999;">
                        You can unsubscribe anytime by visiting our dashboard or replying to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            'subject': subject,
            'body': html_body
        }

    def get_notification_status(self) -> Dict[str, Any]:
        """Get current notification service status"""
        return {
            'is_running': self.is_running,
            'notification_time': self.notification_time,
            'email_configured': bool(self.email_config['email'] and self.email_config['password']),
            'webhook_configured': bool(self.webhook_url),
            'subscriber_count': self.get_subscriber_count(),
            'next_notification': self._get_next_notification_time()
        }
    
    def _get_next_notification_time(self) -> Optional[str]:
        """Get next scheduled notification time"""
        if not self.is_running:
            return None
        
        jobs = schedule.get_jobs()
        if jobs:
            next_run = jobs[0].next_run
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return None

