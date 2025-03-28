"""
Main client for the Pitchfork API wrapper.
"""

from typing import Dict, List, Optional, Union
import logging

from .scraper import PitchforkScraper
from .sentiment import SentimentAnalyzer
from .models.review import Review
from .models.album import Album
from .utils.cache import Cache 


class PitchforkClient:
    """
    Client for accessing Pitchfork music reviews with sentiment analysis.
    """

    def __init__(
        self,
        use_cache: bool = True,
        cache_expiry: int = 86400,
        user_agent: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the Pitchfork client.

        :param use_cache: Whether to use the cache for storing reviews.
        :param cache_expiry: The expiry time for cache items in seconds.
        :param user_agent: The user agent to use for HTTP requests.
        :param verbose: Whether to log debug messages.
        """
        self.scraper = PitchforkScraper(user_agent=user_agent)
        self.sentiment = SentimentAnalyzer()
        self.cache = Cache(enabled=use_cache, expiry=cache_expiry)

        log_level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("pitchfork_api")

    def search_albums(self, query: str) -> List[Album]:
        """
        Search for albums on Pitchfork.

        :param query: The search query.
        :return: A list of Album objects.
        """
        self.logger.info(f"Searching for albums with query: {query}")
        results = self.scarper.search(query)

        albums = [Album.from_search_result(result) for result in results]
        self.cache.set(cache_key, albums)

        return albums

    def get_review(self, url: str, with_sentiment: bool = True) -> Review:
        """
        Get a specific review by URL.

        :param url: The URL of the review.
        :param with_sentiment: Whether to include sentiment analysis.
        :return: A Review object.
        """
        cache_key = f"review:{url}"

        if self.cache.exists(cache_key):
            self.logger.info(f"Loading review from cache: {url}")
            return self.cache.get(cache_key)
        
        self.logger.info(f"Fetching review: {url}")
        review_data = self.scraper.get_review(url)
        review = Review.from_dict(review_data)

        if with_sentiment:
            self.logger.info("Analyzing review sentiment")
            self._add_sentiment_analysis(review)
        
        self.cache.set(cache_key, review)

        return review

    def get_latest_reviews(self, count: int = 10, with_sentiment: bool = True) -> List[Review]:
        """
        Get the latest reviews from Pitchfork.

        :param count: The number of reviews to fetch.
        :param with_sentiment: Whether to include sentiment analysis.
        :return: A list of Review objects.
        """
        cache_key = f"latest:{count}"

        if self.cache.exists(cache_key):
            self.logger.info(f"Using cached latest reviews (count: {count})")
            return self.cache.get(cache_key)

        self.logger.info(f"Fetching {count} latest reviews")
        review_data_list = self.scraper.get_latest_reviews(count)
        reviews = [Review.from_dict(review_data) for data in review_data_list]

        if with_sentiment:
            self.logger.info("Analyzing sentiment for latest reviews")
            for review in reviews:
                self._add_sentiment_analysis(review)
        
        self.cache.set(cache_key, reviews)

        return reviews
    
    def _add_sentiment_analysis(self, review: Review) -> None:
        """
        Add sentiment analysis to a review.

        :param review: The review object.
        """
        review.sentiment = self.sentiment.analyze_text(review.content)
        review.sentiment = sentiment