"""
Flask Web Application for CyberNewsAgent
Main application file with routes and API endpoints
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask import session, redirect, url_for, flash
import logging
from io import BytesIO

from models import NewsItem
from news_agent import CyberNewsAgent
from tools.report_generator import ReportGeneratorTool
from tools.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize the AI agent
cyber_agent = CyberNewsAgent()
report_generator = ReportGeneratorTool()
notification_service = NotificationService()

# Cache for news data (in production, use Redis or similar)
news_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 3600  # 60 minutes to reduce API calls
}

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Check cache
        if (news_cache['data'] is None or 
            news_cache['timestamp'] is None or 
            (datetime.now() - news_cache['timestamp']).seconds > news_cache['cache_duration']):
            
            logger.info("Cache expired, fetching fresh data")
            # Run full pipeline
            result = cyber_agent.run_full_pipeline(max_items=50)
            
            # Update cache
            news_cache['data'] = result
            news_cache['timestamp'] = datetime.now()
        else:
            logger.info("Using cached data")
            result = news_cache['data']
        
        return render_template('index.html', 
                             categorized_news=result['categorized_news'],
                             daily_digest=result['daily_digest'],
                             severity_stats=result['severity_stats'],
                             total_items=result['total_items'],
                             timestamp=result['timestamp'])
    
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash('Error loading news data. Please try again.', 'error')
        return render_template('index.html', 
                             categorized_news={},
                             daily_digest="Unable to load news data.",
                             severity_stats={'High': 0, 'Medium': 0, 'Low': 0},
                             total_items=0,
                             timestamp=datetime.now().isoformat())

@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    results = []
    
    if query and news_cache['data']:
        try:
            results = cyber_agent.search_news(query, news_cache['data']['news_items'])
        except Exception as e:
            logger.error(f"Error searching news: {str(e)}")
            flash('Error searching news. Please try again.', 'error')
    
    return render_template('search.html', query=query, results=results)

@app.route('/digest')
def digest():
    """Daily digest page"""
    digest_text = "No digest available."
    
    if news_cache['data']:
        digest_text = news_cache['data']['daily_digest']
    
    return render_template('digest.html', digest=digest_text)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/notifications')
def notifications():
    """Notifications management page"""
    return render_template('notifications.html')

@app.route('/api/news')
def api_news():
    """API endpoint for news data"""
    try:
        if news_cache['data'] is None:
            return jsonify({'error': 'No news data available'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'news_items': [
                    {
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
                    for item in news_cache['data']['news_items']
                ],
                'categorized_news': {
                    category: [
                        {
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
                        for item in items
                    ]
                    for category, items in news_cache['data']['categorized_news'].items()
                },
                'daily_digest': news_cache['data']['daily_digest'],
                'severity_stats': news_cache['data']['severity_stats'],
                'total_items': news_cache['data']['total_items'],
                'timestamp': news_cache['data']['timestamp']
            }
        })
    
    except Exception as e:
        logger.error(f"Error in API endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/search')
def api_search():
    """API endpoint for news search"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    try:
        if news_cache['data'] is None:
            return jsonify({'error': 'No news data available'}), 404
        
        results = cyber_agent.search_news(query, news_cache['data']['news_items'])
        
        return jsonify({
            'status': 'success',
            'query': query,
            'results': [
                {
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
                for item in results
            ],
            'total_results': len(results)
        })
    
    except Exception as e:
        logger.error(f"Error in search API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/notifications/status')
def notification_status():
    """Get notification service status"""
    try:
        status = notification_service.get_notification_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Notification status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notifications/test', methods=['POST'])
def test_notification():
    """Send a test notification"""
    try:
        success = notification_service.send_test_notification()
        return jsonify({
            'success': success,
            'message': 'Test notification sent successfully' if success else 'Test notification failed'
        })
    except Exception as e:
        logger.error(f"Test notification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notifications/start', methods=['POST'])
def start_notifications():
    """Start daily notifications"""
    try:
        notification_service.start_daily_scheduler()
        return jsonify({
            'success': True,
            'message': 'Daily notifications started'
        })
    except Exception as e:
        logger.error(f"Start notifications error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notifications/stop', methods=['POST'])
def stop_notifications():
    """Stop daily notifications"""
    try:
        notification_service.stop_daily_scheduler()
        return jsonify({
            'success': True,
            'message': 'Daily notifications stopped'
        })
    except Exception as e:
        logger.error(f"Stop notifications error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notifications/subscribe', methods=['POST'])
def subscribe_to_notifications():
    """Subscribe email to daily notifications"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email address is required'
            }), 400
        
        # Validate email format
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Add subscriber to the notification service
        success = notification_service.add_subscriber(email)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully subscribed {email} to daily notifications'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Email already subscribed or subscription failed'
            }), 400
        
    except Exception as e:
        logger.error(f"Subscribe to notifications error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notifications/unsubscribe', methods=['POST'])
def unsubscribe_from_notifications():
    """Unsubscribe email from daily notifications"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email address is required'
            }), 400
        
        # Validate email format
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Remove subscriber from the notification service
        success = notification_service.remove_subscriber(email)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully unsubscribed {email} from daily notifications'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Email not found in subscribers or unsubscription failed'
            }), 400
        
    except Exception as e:
        logger.error(f"Unsubscribe from notifications error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh')
def api_refresh():
    """API endpoint to refresh news data"""
    try:
        logger.info("Refreshing news data via API")
        
        # Run full pipeline
        result = cyber_agent.run_full_pipeline(max_items=50)
        
        # Update cache
        news_cache['data'] = result
        news_cache['timestamp'] = datetime.now()
        
        return jsonify({
            'status': 'success',
            'message': 'News data refreshed successfully',
            'total_items': result['total_items'],
            'timestamp': result['timestamp']
        })
    
    except Exception as e:
        logger.error(f"Error refreshing news data: {str(e)}")
        return jsonify({'error': 'Failed to refresh news data'}), 500

@app.route('/export/pdf')
def export_pdf():
    """Export news as PDF report"""
    try:
        if news_cache['data'] is None:
            flash('No news data available for export.', 'error')
            return redirect(url_for('index'))
        
        # Generate PDF
        pdf_buffer = report_generator.generate_pdf_report(
            news_cache['data']['news_items'],
            f"Cybersecurity News Report - {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"cyber-news-report-{datetime.now().strftime('%Y-%m-%d')}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        flash('Error generating PDF report.', 'error')
        return redirect(url_for('index'))

@app.route('/export/json')
def export_json():
    """Export news as JSON"""
    try:
        if news_cache['data'] is None:
            flash('No news data available for export.', 'error')
            return redirect(url_for('index'))
        
        # Generate JSON
        json_data = report_generator.export_to_json(news_cache['data']['news_items'])
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=cyber-news-{datetime.now().strftime("%Y-%m-%d")}.json'
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating JSON: {str(e)}")
        flash('Error generating JSON export.', 'error')
        return redirect(url_for('index'))

@app.route('/export/email')
def export_email():
    """Generate email summary"""
    try:
        if news_cache['data'] is None:
            flash('No news data available for email summary.', 'error')
            return redirect(url_for('index'))
        
        # Generate email summary
        email_data = report_generator.generate_email_summary(news_cache['data']['news_items'])
        
        return render_template('email_summary.html', 
                             subject=email_data['subject'],
                             body=email_data['body'])
    
    except Exception as e:
        logger.error(f"Error generating email summary: {str(e)}")
        flash('Error generating email summary.', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

@app.template_filter('datetime')
def datetime_filter(value):
    """Template filter for datetime formatting"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    
    return value

@app.template_filter('severity_color')
def severity_color_filter(severity):
    """Template filter for severity color mapping"""
    colors = {
        'High': 'text-red-600 bg-red-100',
        'Medium': 'text-yellow-600 bg-yellow-100',
        'Low': 'text-green-600 bg-green-100'
    }
    return colors.get(severity, 'text-gray-600 bg-gray-100')

@app.template_filter('category_icon')
def category_icon_filter(category):
    """Template filter for category icon mapping"""
    icons = {
        'Latest Attacks': 'fas fa-bomb',
        'Vulnerabilities': 'fas fa-bug',
        'New Tools': 'fas fa-tools',
        'Threat Intelligence': 'fas fa-eye',
        'General': 'fas fa-shield-alt'
    }
    return icons.get(category, 'fas fa-shield-alt')

if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting CyberNewsAgent Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

