"""
Album model for Pitchfork API.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class Album:
    """Represents an album on Pitchfork."""
    
    title: str
    artist: str
    url: str
    score: Optional[float] = None
    year: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    label: Optional[str] = None
    
    @classmethod
    def from_search_result(cls, data: Dict[str, Any]) -> 'Album':
        """
        Create an Album object from a search result dictionary.
        
        Args:
            data: Dictionary with album data from search
            
        Returns:
            Album object
        """
        return cls(
            title=data['title'],
            artist=data['artist'],
            url=data['url'],
            score=data.get('score')
        )
    
    @classmethod
    def from_review(cls, review_data: Dict[str, Any]) -> 'Album':
        """
        Create an Album object from a review dictionary.
        
        Args:
            review_data: Dictionary with review data
            
        Returns:
            Album object
        """
        metadata = review_data.get('metadata', {})
        
        return cls(
            title=review_data['title'],
            artist=review_data['artist'],
            url=review_data['url'],
            score=review_data.get('score'),
            year=metadata.get('year'),
            genres=metadata.get('genres', []),
            label=metadata.get('label')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the album to a dictionary.
        
        Returns:
            Dictionary representation of the album
        """
        return {
            'title': self.title,
            'artist': self.artist,
            'url': self.url,
            'score': self.score,
            'year': self.year,
            'genres': self.genres,
            'label': self.label
        }