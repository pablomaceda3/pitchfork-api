"""
Tests for the SentimentAnalyzer class.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from textblob import TextBlob

from pitchfork_api.sentiment import SentimentAnalyzer


@pytest.fixture
def analyzer():
    """Create a sentiment analyzer instance."""
    with patch('pitchfork_api.sentiment.nltk.download') as mock_download:
        analyzer = SentimentAnalyzer()
        yield analyzer


@pytest.fixture
def sample_positive_text():
    """Create a sample positive review text."""
    return """
    This brilliant album represents a masterpiece of modern music. The innovative approach 
    to composition and production results in stunning soundscapes that captivate the listener 
    from start to finish. Each track offers something exceptional, with standout moments 
    scattered throughout the record.
    """


@pytest.fixture
def sample_negative_text():
    """Create a sample negative review text."""
    return """
    This disappointing album feels mediocre at best. The uninspired songwriting and bland 
    production create a forgettable listening experience. Most tracks are underwhelming, 
    with tedious arrangements that fail to engage the listener. The album suffers from 
    derivative ideas and unimaginative execution.
    """


class TestSentimentAnalyzer:
    """Tests for the SentimentAnalyzer class."""
    
    def test_initialization(self, analyzer):
        """Test that analyzer initializes correctly."""
        assert hasattr(analyzer, 'POSITIVE_TERMS')
        assert hasattr(analyzer, 'NEGATIVE_TERMS')
        assert hasattr(analyzer, 'logger')
    
    def test_analyze_positive_text(self, analyzer, sample_positive_text):
        """Test analyzing positive text."""
        # Call the function under test
        result = analyzer.analyze_text(sample_positive_text)
        
        # Verify the results
        assert result['polarity'] > 0.5
        assert result['assessment'] in ('positive', 'very positive')
        assert len(result['key_terms']) > 0
        assert any(term['term'] == 'brilliant' for term in result['key_terms'])
        assert any(term['term'] == 'masterpiece' for term in result['key_terms'])
        assert len(result['sentences']) > 0
    
    def test_analyze_negative_text(self, analyzer, sample_negative_text):
        """Test analyzing negative text."""
        # Call the function under test
        result = analyzer.analyze_text(sample_negative_text)
        
        # Verify the results
        assert result['polarity'] < -0.2
        assert result['assessment'] in ('negative', 'very negative')
        assert len(result['key_terms']) > 0
        assert any(term['term'] == 'disappointing' for term in result['key_terms'])
        assert any(term['term'] == 'mediocre' for term in result['key_terms'])
        assert len(result['sentences']) > 0
    
    def test_analyze_empty_text(self, analyzer):
        """Test analyzing empty text."""
        # Call the function under test
        result = analyzer.analyze_text("")
        
        # Verify the results
        assert result['polarity'] == 0.0
        assert result['subjectivity'] == 0.0
        assert result['assessment'] == 'neutral'
        assert len(result['key_terms']) == 0
        assert len(result['sentences']) == 0
    
    def test_get_assessment(self, analyzer):
        """Test the _get_assessment method."""
        assessments = [
            (0.8, 'very positive'),
            (0.5, 'positive'),
            (0.0, 'neutral'),
            (-0.3, 'negative'),
            (-0.8, 'very negative')
        ]
        
        for polarity, expected in assessments:
            assert analyzer._get_assessment(polarity) == expected
    
    def test_extract_key_terms(self, analyzer, sample_positive_text, sample_negative_text):
        """Test the _extract_key_terms method."""
        # Test positive terms
        positive_terms = analyzer._extract_key_terms(sample_positive_text)
        assert any(term['term'] == 'brilliant' and term['sentiment'] == 'positive' for term in positive_terms)
        
        # Test negative terms
        negative_terms = analyzer._extract_key_terms(sample_negative_text)
        assert any(term['term'] == 'disappointing' and term['sentiment'] == 'negative' for term in negative_terms)
    
    def test_analyze_sentences(self, analyzer):
        """Test the _analyze_sentences method."""
        # Create test sentences
        sentences = [
            TextBlob("This is a brilliant album."),
            TextBlob("The songwriting is mediocre."),
            TextBlob("Some tracks are okay.")
        ]
        
        # Call the function under test
        result = analyzer._analyze_sentences(sentences)
        
        # Verify the results
        assert len(result) > 0
        # Sentences should be sorted by absolute polarity (most extreme first)
        assert abs(result[0]['polarity']) >= abs(result[-1]['polarity']) if len(result) > 1 else True
    
    @patch('pitchfork_api.sentiment.pd.DataFrame')
    def test_get_summary_stats(self, mock_df, analyzer):
        """Test the get_summary_stats method."""
        # Create mock reviews with sentiment data
        reviews = [
            {
                'title': 'Album 1',
                'artist': 'Artist 1',
                'score': 8.5,
                'sentiment': {
                    'polarity': 0.6,
                    'subjectivity': 0.7,
                    'assessment': 'positive'
                }
            },
            {
                'title': 'Album 2',
                'artist': 'Artist 2',
                'score': 4.0,
                'sentiment': {
                    'polarity': -0.4,
                    'subjectivity': 0.8,
                    'assessment': 'negative'
                }
            }
        ]
        
        # Mock the DataFrame and its operations
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        
        # Configure mock return values
        mock_df_instance['polarity'].mean.return_value = 0.1
        mock_df_instance['subjectivity'].mean.return_value = 0.75
        mock_df_instance[['score', 'polarity']].corr.return_value = pd.DataFrame([[1.0, 0.85], [0.85, 1.0]])
        
        # Set up idxmax and idxmin
        mock_df_instance['polarity'].idxmax.return_value = 0
        mock_df_instance['polarity'].idxmin.return_value = 1
        mock_df_instance.loc.__getitem__.side_effect = [
            reviews[0],  # idxmax result
            reviews[1]   # idxmin result
        ]
        
        # Call the function under test
        result = analyzer.get_summary_stats(reviews)
        
        # Verify the results
        assert result['avg_polarity'] == 0.1
        assert result['avg_subjectivity'] == 0.75
        assert result['correlation_score_sentiment'] == 0.85
        assert 'most_positive' in result
        assert 'most_negative' in result