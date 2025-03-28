"""
Tests for the PitchforkClient class.
"""

import pytest
from unittest.mock import patch, MagicMock

from pitchfork_api.client import PitchforkClient
from pitchfork_api.models.album import Album
from pitchfork_api.models.review import Review


@pytest.fixture
def client():
    """Create a client instance with mocked components."""
    with patch('pitchfork_api.client.PitchforkScraper') as mock_scraper, \
         patch('pitchfork_api.client.SentimentAnalyzer') as mock_sentiment, \
         patch('pitchfork_api.client.Cache') as mock_cache:
        
        # Configure the mocks
        mock_scraper_instance = mock_scraper.return_value
        mock_sentiment_instance = mock_sentiment.return_value
        mock_cache_instance = mock_cache.return_value
        
        # Return the client with mocked components
        yield PitchforkClient(), mock_scraper_instance, mock_sentiment_instance, mock_cache_instance


class TestPitchforkClient:
    """Tests for the PitchforkClient class."""
    
    def test_search(self, client):
        """Test the search method."""
        client_instance, mock_scraper, mock_sentiment, mock_cache = client
        
        # Configure mock cache to simulate a cache miss
        mock_cache.exists.return_value = False
        
        # Configure mock scraper to return search results
        mock_results = [
            {'title': 'OK Computer', 'artist': 'Radiohead', 'url': 'https://pitchfork.com/reviews/radiohead-ok-computer', 'score': 10.0},
            {'title': 'Kid A', 'artist': 'Radiohead', 'url': 'https://pitchfork.com/reviews/radiohead-kid-a', 'score': 9.5}
        ]
        mock_scraper.search.return_value = mock_results
        
        # Call the function under test
        results = client_instance.search("Radiohead")
        
        # Verify the results
        assert len(results) == 2
        assert all(isinstance(result, Album) for result in results)
        assert results[0].title == 'OK Computer'
        assert results[1].title == 'Kid A'
        
        # Verify the mocks were called correctly
        mock_cache.exists.assert_called_once()
        mock_scraper.search.assert_called_once_with("Radiohead")
        mock_cache.set.assert_called_once()
    
    def test_search_cache_hit(self, client):
        """Test the search method with a cache hit."""
        client_instance, mock_scraper, mock_sentiment, mock_cache = client
        
        # Configure mock cache to simulate a cache hit
        mock_cache.exists.return_value = True
        cached_results = [
            Album(title='OK Computer', artist='Radiohead', url='https://pitchfork.com/reviews/radiohead-ok-computer', score=10.0),
            Album(title='Kid A', artist='Radiohead', url='https://pitchfork.com/reviews/radiohead-kid-a', score=9.5)
        ]
        mock_cache.get.return_value = cached_results
        
        # Call the function under test
        results = client_instance.search("Radiohead")
        
        # Verify the results
        assert len(results) == 2
        assert results == cached_results
        
        # Verify cache was used (scraper not called)
        mock_cache.exists.assert_called_once()
        mock_cache.get.assert_called_once()
        mock_scraper.search.assert_not_called()
    
    def test_get_review(self, client):
        """Test the get_review method."""
        client_instance, mock_scraper, mock_sentiment, mock_cache = client
        
        # Configure mock cache to simulate a cache miss
        mock_cache.exists.return_value = False
        
        # Configure mock scraper to return a review
        review_data = {
            'title': 'OK Computer',
            'artist': 'Radiohead',
            'url': 'https://pitchfork.com/reviews/radiohead-ok-computer',
            'score': 10.0,
            'content': 'A groundbreaking album that defined a generation.',
            'published_date': '1997-06-01',
            'metadata': {'label': 'XL Recordings', 'year': 1997, 'genres': ['Rock', 'Alternative']},
            'tracks': []
        }
        mock_scraper.get_review.return_value = review_data
        
        # Call the function under test
        review = client_instance.get_review('https://pitchfork.com/reviews/radiohead-ok-computer')
        
        # Verify the results
        assert isinstance(review, Review)
        assert review.title == 'OK Computer'
        assert review.artist == 'Radiohead'
        assert review.score == 10.0
        
        # Verify the mocks were called correctly
        mock_cache.exists.assert_called_once()
        mock_scraper.get_review.assert_called_once()
        mock_sentiment.analyze_text.assert_called_once()
        mock_cache.set.assert_called_once()
    
    def test_get_latest_reviews(self, client):
        """Test the get_latest_reviews method."""
        client_instance, mock_scraper, mock_sentiment, mock_cache = client
        
        # Configure mock cache to simulate a cache miss
        mock_cache.exists.return_value = False
        
        # Configure mock scraper to return review data
        review_data_list = [
            {
                'title': 'New Album 1',
                'artist': 'Artist 1',
                'url': 'https://pitchfork.com/reviews/new-album-1',
                'score': 8.5,
                'content': 'A solid effort from Artist 1.',
                'published_date': '2023-01-01',
                'metadata': {},
                'tracks': []
            },
            {
                'title': 'New Album 2',
                'artist': 'Artist 2',
                'url': 'https://pitchfork.com/reviews/new-album-2',
                'score': 7.8,
                'content': 'Artist 2 returns with a fresh sound.',
                'published_date': '2023-01-02',
                'metadata': {},
                'tracks': []
            }
        ]
        mock_scraper.get_latest_reviews.return_value = review_data_list
        
        # Call the function under test
        reviews = client_instance.get_latest_reviews(count=2)
        
        # Verify the results
        assert len(reviews) == 2
        assert all(isinstance(review, Review) for review in reviews)
        assert reviews[0].title == 'New Album 1'
        assert reviews[1].title == 'New Album 2'
        
        # Verify the mocks were called correctly
        mock_cache.exists.assert_called_once()
        mock_scraper.get_latest_reviews.assert_called_once_with(2)
        assert mock_sentiment.analyze_text.call_count == 2
        mock_cache.set.assert_called_once()