"""
Parsing utilities for Pitchfork API.
"""

import re
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger("pitchfork_api.utils.parsing")


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
        
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove extra whitespace
    text = text.strip()
    
    return text


def extract_date(date_str: str) -> Optional[datetime]:
    """
    Extract and parse date from string.
    
    Args:
        date_str: Date string
        
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        pass
        
    # Try common formats
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%B %d, %Y',
        '%b %d, %Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    logger.warning(f"Could not parse date: {date_str}")
    return None


def normalize_url(url: str, base_url: str) -> str:
    """
    Normalize URL by ensuring it has a proper domain.
    
    Args:
        url: URL to normalize
        base_url: Base URL to use if url is relative
        
    Returns:
        Normalized URL
    """
    if url.startswith('http'):
        return url
        
    # Handle relative URLs
    if url.startswith('/'):
        return f"{base_url.rstrip('/')}{url}"
    else:
        return f"{base_url.rstrip('/')}/{url}"


def extract_score(score_text: str) -> Optional[float]:
    """
    Extract numeric score from text.
    
    Args:
        score_text: Score text
        
    Returns:
        Score as float or None if extraction fails
    """
    if not score_text:
        return None
        
    # Try to find decimal number in the text
    match = re.search(r'(\d+\.\d+)', score_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
            
    # Try to find integer
    match = re.search(r'(\d+)', score_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
            
    logger.warning(f"Could not extract score from: {score_text}")
    return None