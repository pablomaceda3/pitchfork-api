"""
Web scraper for Pitchfork music reviews.
"""

import time
import random
from typing import Dict, List, Any, Optional
import re
import logging

import requests
from bs4 import BeautifulSoup

from .utils.parsing import clean_text, extract_date, normalize_url


class PitchforkScraper:
    """
    Scraper for extracting data from Pitchfork website.
    """
    
    BASE_URL = "https://pitchfork.com"
    SEARCH_URL = f"{BASE_URL}/search/"
    REVIEWS_URL = f"{BASE_URL}/reviews/albums/"
    
    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialize the Pitchfork scraper.
        
        Args:
            user_agent: Custom user agent string for requests
        """
        self.logger = logging.getLogger("pitchfork_api.scraper")
        
        # Set up session with headers
        self.session = requests.Session()
        default_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session.headers.update({
            "User-Agent": user_agent or default_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for albums on Pitchfork.
        
        Args:
            query: Search query string
            
        Returns:
            List of search result dictionaries
        """
        params = {
            "query": query,
            "filter": "albumreviews",
        }
        
        response = self._make_request(self.SEARCH_URL, params=params)
        soup = BeautifulSoup(response.content, "lxml")
        
        results = []
        search_results = soup.select(".search-results article")
        
        for result in search_results:
            try:
                # Extract data from search result
                title_elem = result.select_one("h2.title")
                artist_elem = result.select_one(".artist-list")
                link_elem = result.select_one("a.review__link")
                score_elem = result.select_one(".score")
                
                if not all([title_elem, artist_elem, link_elem]):
                    continue
                
                album_data = {
                    "title": clean_text(title_elem.text),
                    "artist": clean_text(artist_elem.text),
                    "url": normalize_url(link_elem["href"], self.BASE_URL),
                    "score": float(score_elem.text) if score_elem else None,
                }
                
                results.append(album_data)
            except Exception as e:
                self.logger.warning(f"Error parsing search result: {e}")
                continue
                
        return results
    
    def get_review(self, url: str) -> Dict[str, Any]:
        """
        Get a review by URL.
        
        Args:
            url: URL of the review
            
        Returns:
            Dictionary with review data
        """
        response = self._make_request(url)
        soup = BeautifulSoup(response.content, "lxml")
        
        try:
            # Basic review information
            title_elem = soup.select_one("h1.review-title")
            artist_elem = soup.select_one("h2.artist-links")
            score_elem = soup.select_one("p.score")
            content_elem = soup.select_one(".review-detail__text")
            published_elem = soup.select_one("time.pub-date")
            
            if not all([title_elem, artist_elem, content_elem]):
                raise ValueError("Missing essential review elements")
            
            # Extract review metadata
            metadata = self._extract_metadata(soup)
            
            # Extract track reviews if available
            tracks = self._extract_tracks(soup)
            
            review_data = {
                "title": clean_text(title_elem.text),
                "artist": clean_text(artist_elem.text),
                "score": float(score_elem.text) if score_elem else None,
                "content": clean_text(content_elem.get_text(" ", strip=True)),
                "url": url,
                "published_date": extract_date(published_elem["datetime"]) if published_elem else None,
                "metadata": metadata,
                "tracks": tracks,
            }
            
            return review_data
        except Exception as e:
            self.logger.error(f"Error parsing review at {url}: {e}")
            raise
    
    def get_latest_reviews(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the latest album reviews.
        
        Args:
            count: Number of reviews to fetch
            
        Returns:
            List of review dictionaries
        """
        reviews = []
        page = 1
        
        while len(reviews) < count:
            # Get review URLs from the current page
            urls = self._get_review_urls_from_page(page)
            if not urls:
                break
                
            # Fetch each review
            for url in urls:
                if len(reviews) >= count:
                    break
                    
                try:
                    review = self.get_review(url)
                    reviews.append(review)
                    
                    # Be nice to the server
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception as e:
                    self.logger.warning(f"Error fetching review at {url}: {e}")
                    continue
            
            page += 1
            
        return reviews[:count]
    
    def _get_review_urls_from_page(self, page: int = 1) -> List[str]:
        """
        Get review URLs from a page of album reviews.
        
        Args:
            page: Page number
            
        Returns:
            List of review URLs
        """
        params = {"page": page}
        response = self._make_request(self.REVIEWS_URL, params=params)
        soup = BeautifulSoup(response.content, "lxml")
        
        review_links = soup.select("a.review__link")
        urls = [normalize_url(link["href"], self.BASE_URL) for link in review_links]
        
        return urls
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract metadata from a review page.
        
        Args:
            soup: BeautifulSoup object of the review page
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Try to find metadata section
        meta_section = soup.select_one(".single-album-tombstone__meta-year")
        if meta_section:
            # Extract label and year
            meta_text = clean_text(meta_section.text)
            label_match = re.search(r"([^•]+)•\s*(\d{4})", meta_text)
            
            if label_match:
                metadata["label"] = label_match.group(1).strip()
                metadata["year"] = int(label_match.group(2))
                
        # Try to find genres
        genre_elems = soup.select(".genre-list__link")
        if genre_elems:
            metadata["genres"] = [clean_text(elem.text) for elem in genre_elems]
            
        return metadata
    
    def _extract_tracks(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract track information if available.
        
        Args:
            soup: BeautifulSoup object of the review page
            
        Returns:
            List of track dictionaries
        """
        tracks = []
        
        # Look for track review section
        track_section = soup.select_one(".track-reviews")
        if not track_section:
            return tracks
            
        track_items = track_section.select(".track-review")
        for item in track_items:
            try:
                title_elem = item.select_one(".track-review__title")
                content_elem = item.select_one(".track-review__text")
                
                if title_elem:
                    track = {
                        "title": clean_text(title_elem.text),
                        "content": clean_text(content_elem.text) if content_elem else "",
                    }
                    tracks.append(track)
            except Exception as e:
                self.logger.warning(f"Error parsing track: {e}")
                continue
                
        return tracks
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make an HTTP request with error handling and rate limiting.
        
        Args:
            url: URL to request
            params: Optional query parameters
            
        Returns:
            Response object
        """
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise