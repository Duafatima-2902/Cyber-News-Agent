#!/usr/bin/env python3
"""
Railway start script for CyberNewsAgent
"""

import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting CyberNewsAgent on Railway (port {port})")
    print("✅ Full functionality available:")
    print("📧 - Email subscriptions with persistent storage")
    print("⏰ - Daily notifications at 9:00 AM")
    print("📰 - News fetching from multiple sources")
    print("🤖 - AI-powered analysis and categorization")
    print("📊 - Professional HTML email reports")
    
    app.run(host='0.0.0.0', port=port, debug=False)