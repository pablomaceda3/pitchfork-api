"""
Review model for Pitchfork API.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class Track:
    """Track reviewed within an album review."""
    
    title: str
    content: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None


@dataclass
class Review:
    """Represents a Pitchfork album review."""
    
    title: str
    artist: str
    url: str
    content: str
    score: Optional[float] = None
    published_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tracks: List[Track] = field(default_factory=list)
    sentiment: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """
        Create a Review object from a dictionary.
        
        Args:
            data: Dictionary with review data
            
        Returns:
            Review object
        """
        # Process tracks if available
        tracks = []
        if 'tracks' in data and data['tracks']:
            tracks = [Track(**track_data) for track_data in data['tracks']]
            
        # Create the review object
        review_data = {
            'title': data['title'],
            'artist': data['artist'],
            'url': data['url'],
            'content': data['content'],
            'score': data.get('score'),
            'published_date': data.get('published_date'),
            'metadata': data.get('metadata', {}),
            'tracks': tracks,
            'sentiment': data.get('sentiment')
        }
        
        return cls(**review_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the review to a dictionary.
        
        Returns:
            Dictionary representation of the review
        """
        return {
            'title': self.title,
            'artist': self.artist,
            'url': self.url,
            'content': self.content,
            'score': self.score,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'metadata': self.metadata,
            'tracks': [
                {
                    'title': track.title,
                    'content': track.content,
                    'sentiment': track.sentiment
                }
                for track in self.tracks
            ],
            'sentiment': self.sentiment
        }
    
    @property
    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of the review.
        
        Returns:
            Dictionary with review summary
        """
        return {
            'title': self.title,
            'artist': self.artist,
            'score': self.score,
            'url': self.url,
            'published_date': self.published_date.strftime('%Y-%m-%d') if self.published_date else None,
            'genres': self.metadata.get('genres', []),
            'sentiment_assessment': self.sentiment.get('assessment') if self.sentiment else None
        }