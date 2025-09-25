"""
Data models for CyberNewsAgent
Contains data classes used throughout the application
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class NewsItem:
    """Data class for news items"""
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    category: str
    severity: str
    tags: List[str]
    summary: str = ""

