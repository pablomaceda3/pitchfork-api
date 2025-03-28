"""
Sentiment analysis for Pitchfork reviews.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import nltk
from textblob import TextBlob
import pandas as pd


class SentimentAnalyzer:
    """
    Analyzes sentiment of Pitchfork reviews.
    """
    
    # Common positive and negative music review terms
    POSITIVE_TERMS = [
        "masterpiece", "brilliant", "exceptional", "outstanding", "innovative",
        "groundbreaking", "excellent", "superb", "stunning", "impressive",
        "perfect", "visionary", "captivating", "spectacular", "remarkable"
    ]
    
    NEGATIVE_TERMS = [
        "disappointing", "mediocre", "uninspired", "bland", "derivative",
        "forgettable", "underwhelming", "tedious", "redundant", "unimaginative",
        "generic", "lackluster", "monotonous", "dull", "pretentious"
    ]
    
    def __init__(self):
        """Initialize the sentiment analyzer and ensure NLTK resources are available."""
        self.logger = logging.getLogger("pitchfork_api.sentiment")
        
        # Ensure required NLTK resources are available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer")
            nltk.download('punkt', quiet=True)
            
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of review text.
        
        Args:
            text: The review text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not text:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "assessment": "neutral",
                "key_terms": [],
                "sentences": [],
            }
            
        # Break text into sentences and analyze each one
        blob = TextBlob(text)
        
        # Calculate overall sentiment
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Map to qualitative assessment
        assessment = self._get_assessment(polarity)
        
        # Find key terms that influence sentiment
        key_terms = self._extract_key_terms(text)
        
        # Analyze individual sentences
        sentence_analysis = self._analyze_sentences(blob.sentences)
        
        return {
            "polarity": round(polarity, 2),
            "subjectivity": round(subjectivity, 2),
            "assessment": assessment,
            "key_terms": key_terms,
            "sentences": sentence_analysis,
        }
        
    def _get_assessment(self, polarity: float) -> str:
        """
        Convert polarity score to qualitative assessment.
        
        Args:
            polarity: Sentiment polarity score (-1 to 1)
            
        Returns:
            Qualitative assessment string
        """
        if polarity >= 0.6:
            return "very positive"
        elif polarity >= 0.2:
            return "positive"
        elif polarity > -0.2:
            return "neutral"
        elif polarity > -0.6:
            return "negative"
        else:
            return "very negative"
            
    def _extract_key_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key terms that influence sentiment.
        
        Args:
            text: Review text
            
        Returns:
            List of key terms with their sentiment impact
        """
        text = text.lower()
        key_terms = []
        
        # Check for domain-specific positive terms
        for term in self.POSITIVE_TERMS:
            if term in text:
                key_terms.append({
                    "term": term,
                    "sentiment": "positive",
                    "count": len(re.findall(r'\b' + re.escape(term) + r'\b', text))
                })
                
        # Check for domain-specific negative terms
        for term in self.NEGATIVE_TERMS:
            if term in text:
                key_terms.append({
                    "term": term,
                    "sentiment": "negative",
                    "count": len(re.findall(r'\b' + re.escape(term) + r'\b', text))
                })
                
        # Sort by occurrence count
        key_terms.sort(key=lambda x: x["count"], reverse=True)
        
        return key_terms[:10]  # Return top 10 terms
        
    def _analyze_sentences(self, sentences: List[TextBlob]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of individual sentences.
        
        Args:
            sentences: List of TextBlob sentences
            
        Returns:
            List of sentence sentiment analysis dictionaries
        """
        sentence_analysis = []
        
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.words) < 3:
                continue
                
            polarity = sentence.sentiment.polarity
            subjectivity = sentence.sentiment.subjectivity
            
            # Only include sentences with strong sentiment
            if abs(polarity) > 0.3:
                sentence_analysis.append({
                    "text": str(sentence),
                    "polarity": round(polarity, 2),
                    "subjectivity": round(subjectivity, 2),
                    "assessment": self._get_assessment(polarity)
                })
                
        # Sort by polarity (most extreme first)
        sentence_analysis.sort(key=lambda x: abs(x["polarity"]), reverse=True)
        
        return sentence_analysis[:5]  # Return top 5 significant sentences
        
    def get_summary_stats(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for a collection of reviews.
        
        Args:
            reviews: List of review dictionaries with sentiment data
            
        Returns:
            Dictionary with summary statistics
        """
        if not reviews:
            return {}
            
        # Extract polarities and create DataFrame
        data = []
        for review in reviews:
            if "sentiment" in review and review["sentiment"]:
                data.append({
                    "title": review.get("title", "Unknown"),
                    "artist": review.get("artist", "Unknown"),
                    "score": review.get("score", None),
                    "polarity": review["sentiment"].get("polarity", 0),
                    "subjectivity": review["sentiment"].get("subjectivity", 0),
                })
                
        if not data:
            return {}
            
        df = pd.DataFrame(data)
        
        # Calculate statistics
        stats = {
            "avg_polarity": round(df["polarity"].mean(), 2),
            "avg_subjectivity": round(df["subjectivity"].mean(), 2),
            "correlation_score_sentiment": round(df[["score", "polarity"]].corr().iloc[0, 1], 2),
            "most_positive": df.loc[df["polarity"].idxmax()].to_dict() if not df.empty else None,
            "most_negative": df.loc[df["polarity"].idxmin()].to_dict() if not df.empty else None,
        }
        
        return stats