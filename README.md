# 🛡️ CyberNewsAgent

An AI-powered cybersecurity news aggregator that collects, analyzes, and delivers daily cybersecurity updates via email. **Deployed on Railway for full functionality!**

## ✨ Features

- 🔍 **News Collection**: Multiple sources (RSS feeds, Reddit, web scraping)
- 🤖 **AI Analysis**: Google Gemini integration with fallback to templates
- 📧 **Email Notifications**: Daily digest at 9:00 AM with welcome emails
- 🌐 **Web Interface**: Clean, responsive dashboard
- 📱 **Mobile Friendly**: Works on all devices
- 🚀 **Railway Deployed**: Full functionality with persistent storage

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- API Keys (all FREE):
  - Google Gemini API
  - News API
  - Reddit API (optional)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd cyber-news-agent
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys
   ```

3. **Run locally**:
   ```bash
   python start.py
   ```

4. **Access**: http://localhost:5000

## 🌐 Railway Deployment (RECOMMENDED)

Railway is **perfect** for this Flask app:

- ✅ **Full Flask support** with persistent storage
- ✅ **Background tasks** (daily notifications work)
- ✅ **Free tier** (500 hours/month)
- ✅ **Easy deployment** from GitHub
- ✅ **Custom domains** and SSL

### Deploy to Railway:

1. **Create Railway Account**: [railway.app](https://railway.app)
2. **Connect GitHub**: Deploy from your repository
3. **Set Environment Variables** (11 total):
   ```
   FLASK_ENV=production
   GEMINI_API_KEY=your_gemini_api_key
   NEWS_API_KEY=your_newsapi_key
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   SECRET_KEY=your_secret_key
   NOTIFICATION_TIME=09:00
   NOTIFICATION_EMAIL=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   CUSTOM_NEWS_SOURCES=https://krebsonsecurity.com/feed/,https://feeds.feedburner.com/SecurityWeek
   APP_URL=https://your-app-name.railway.app
   ```
4. **Deploy**: Railway auto-detects Python app and deploys!

## 📋 API Keys Setup

### 1. Google Gemini API (FREE)
- Visit: https://makersuite.google.com/app/apikey
- Create API key
- Add to `.env`: `GEMINI_API_KEY=your_key_here`

### 2. News API (FREE)
- Visit: https://newsapi.org/register
- Get API key
- Add to `.env`: `NEWS_API_KEY=your_key_here`

### 3. Reddit API (FREE)
- Visit: https://www.reddit.com/prefs/apps
- Create app
- Add to `.env`:
  ```
  REDDIT_CLIENT_ID=your_client_id
  REDDIT_CLIENT_SECRET=your_client_secret
  ```

### 4. Email Configuration
- Use Gmail with App Password
- Add to `.env`:
  ```
  NOTIFICATION_EMAIL=your_email@gmail.com
  EMAIL_PASSWORD=your_app_password
  ```

## 📱 Usage

### Web Interface
- **Dashboard**: View latest cybersecurity news
- **Notifications**: Subscribe to daily email digests
- **Search**: Find specific topics

### Email Subscriptions
1. **Subscribe**: Enter email on `/notifications` page
2. **Welcome Email**: Instant confirmation with engaging content
3. **Daily Emails**: Professional HTML digest at 9:00 AM
4. **Unsubscribe**: Easy removal anytime

## 📊 Project Structure

```
cyber-news-agent/
├── app.py                 # Main Flask application
├── start.py               # Railway start script
├── models.py              # Data models
├── news_agent.py          # Core news processing
├── requirements.txt       # Dependencies
├── railway.json           # Railway configuration
├── Procfile               # Process file
├── runtime.txt            # Python version
├── nixpacks.toml         # Build configuration
├── pyproject.toml        # Python project config
├── templates/             # HTML templates
├── static/               # CSS, JS, images
├── tools/                # Core tools
│   ├── news_api.py       # News API integration
│   ├── web_scraper.py    # Web scraping
│   ├── reddit_api.py     # Reddit integration
│   ├── summarizer.py     # AI analysis
│   ├── report_generator.py # Email generation
│   └── notification_service.py # Email service
└── subscribers.txt       # Email subscribers
```

## 🔧 Configuration

### Environment Variables
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key
NEWS_API_KEY=your_newsapi_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key

# Notification Settings
NOTIFICATION_TIME=09:00
NOTIFICATION_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Railway Deployment
APP_URL=https://your-app-name.railway.app

# Optional: Custom News Sources
CUSTOM_NEWS_SOURCES=https://krebsonsecurity.com/feed/,https://feeds.feedburner.com/SecurityWeek
```

## 🚨 Troubleshooting

### Common Issues
1. **API Key Errors**: Verify all keys in `.env`
2. **Email Not Sending**: Check Gmail App Password
3. **News Not Loading**: Check internet connection
4. **AI Analysis Failing**: App falls back to templates automatically

### Railway Issues
- **Build Failed**: Check `requirements.txt` and file structure
- **Service Won't Start**: Verify start command and environment variables
- **Files Not Found**: Ensure files are in repository root (not subdirectories)

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini**: AI analysis and summarization
- **News API**: News data source
- **Reddit**: Community discussions
- **Flask**: Web framework
- **Railway**: Hosting platform

---

**Built with ❤️ for the cybersecurity community**

🛡️ Stay informed, stay secure! 🛡️