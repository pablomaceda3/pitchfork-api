"""
Tests for the PitchforkScraper class.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from pitchfork_api.scraper import PitchforkScraper


@pytest.fixture
def sample_review_html():
    """Load sample review HTML from fixtures."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(current_dir, 'fixtures', 'sample_review.html')
    
    # Create a fallback if the fixture file doesn't exist
    if not os.path.exists(fixture_path):
        return """
        <html>
            <head><title>Sample Review</title></head>
            <body>
                <h1 class="review-title">OK Computer</h1>
                <h2 class="artist-links">Radiohead</h2>
                <p class="score">10.0</p>
                <div class="review-detail__text">
                    <p>A groundbreaking album that defined a generation.</p>
                </div>
                <time class="pub-date" datetime="1997-06-01T00:00:00Z"></time>
                <div class="single-album-tombstone__meta-year">XL Recordings • 1997</div>
                <div class="genre-list">
                    <a class="genre-list__link">Rock</a>
                    <a class="genre-list__link">Alternative</a>
                </div>
            </body>
        </html>
        """
    
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def sample_search_html():
    """Create sample search results HTML."""
    return """
    <html>
        <div class="search-results">
            <article>
                <h2 class="title">OK Computer</h2>
                <div class="artist-list">Radiohead</div>
                <a class="review__link" href="/reviews/albums/radiohead-ok-computer/">Read Review</a>
                <div class="score">10.0</div>
            </article>
            <article>
                <h2 class="title">Kid A</h2>
                <div class="artist-list">Radiohead</div>
                <a class="review__link" href="/reviews/albums/radiohead-kid-a/">Read Review</a>
                <div class="score">9.5</div>
            </article>
        </div>
    </html>
    """


@pytest.fixture
def scraper():
    """Create a scraper instance with mocked requests session."""
    with patch('pitchfork_api.scraper.requests.Session') as mock_session:
        scraper = PitchforkScraper()
        mock_session_instance = mock_session.return_value
        
        # Configure the mock
        scraper.session = mock_session_instance
        
        yield scraper, mock_session_instance


class TestPitchforkScraper:
    """Tests for the PitchforkScraper class."""
    
    def test_init(self):
        """Test initializing the scraper."""
        scraper = PitchforkScraper(user_agent="Test Agent")
        assert scraper.BASE_URL == "https://pitchfork.com"
        assert "User-Agent" in scraper.session.headers
        assert scraper.session.headers["User-Agent"] == "Test Agent"
    
    def test_search(self, scraper, sample_search_html):
        """Test the search method."""
        scraper_instance, mock_session = scraper
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = sample_search_html.encode('utf-8')
        mock_session.get.return_value = mock_response
        
        # Call the function under test
        results = scraper_instance.search("Radiohead")
        
        # Verify the results
        assert len(results) == 2
        assert results[0]['title'] == 'OK Computer'
        assert results[0]['artist'] == 'Radiohead'
        assert results[0]['score'] == 10.0
        assert results[1]['title'] == 'Kid A'
        
        # Verify the mock was called correctly
        mock_session.get.assert_called_once()
        assert mock_session.get.call_args[0][0] == scraper_instance.SEARCH_URL
    
    def test_get_review(self, scraper, sample_review_html):
        """Test the get_review method."""
        scraper_instance, mock_session = scraper
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = sample_review_html.encode('utf-8')
        mock_session.get.return_value = mock_response
        
        # Call the function under test
        review = scraper_instance.get_review("https://pitchfork.com/reviews/albums/radiohead-ok-computer/")
        
        # Verify the results
        assert review['title'] == 'OK Computer'
        assert review['artist'] == 'Radiohead'
        assert review['score'] == 10.0
        assert 'groundbreaking' in review['content']
        assert review['metadata'].get('year') == 1997
        assert 'Rock' in review['metadata'].get('genres', [])
        
        # Verify the mock was called correctly
        mock_session.get.assert_called_once_with(
            "https://pitchfork.com/reviews/albums/radiohead-ok-computer/", 
            params=None, 
            timeout=10
        )
    
    def test_extract_metadata(self, scraper, sample_review_html):
        """Test the _extract_metadata method."""
        scraper_instance, _ = scraper
        
        # Parse the HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_review_html, 'lxml')
        
        # Call the function under test
        metadata = scraper_instance._extract_metadata(soup)
        
        # Verify the results
        assert metadata['label'] == 'XL Recordings'
        assert metadata['year'] == 1997
        assert 'Rock' in metadata['genres']
        assert 'Alternative' in metadata['genres']
    
    def test_make_request_error(self, scraper):
        """Test handling of request errors."""
        scraper_instance, mock_session = scraper
        
        # Mock a request exception
        mock_session.get.side_effect = Exception("Connection error")
        
        # Call the function under test and verify exception
        with pytest.raises(Exception):
            scraper_instance._make_request("https://example.com")