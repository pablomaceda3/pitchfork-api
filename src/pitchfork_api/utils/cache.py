"""
Caching utilities for Pitchfork API.
"""

import os
import json
import time
import logging
from typing import Any, Dict, Optional
import pickle
from pathlib import Path


class Cache:
    """
    Simple file-based cache for Pitchfork API data.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        expiry: int = 86400,  # 24 hours in seconds
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the cache.
        
        Args:
            enabled: Whether caching is enabled
            expiry: Cache expiry time in seconds
            cache_dir: Directory to store cache files
        """
        self.enabled = enabled
        self.expiry = expiry
        self.logger = logging.getLogger("pitchfork_api.cache")
        
        # Set up cache directory
        if not cache_dir:
            home_dir = str(Path.home())
            cache_dir = os.path.join(home_dir, ".pitchfork_api", "cache")
            
        self.cache_dir = cache_dir
        
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.logger.info(f"Cache initialized at {self.cache_dir}")
    
    def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.exists(key):
            return None
            
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                
            # Check if expired
            if time.time() - data['timestamp'] > self.expiry:
                self.logger.debug(f"Cache expired for key: {key}")
                self._remove_file(cache_path)
                return None
                
            self.logger.debug(f"Cache hit for key: {key}")
            return data['value']
        except Exception as e:
            self.logger.warning(f"Error reading cache for key {key}: {e}")
            self._remove_file(cache_path)
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                'timestamp': time.time(),
                'value': value
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
                
            self.logger.debug(f"Cached value for key: {key}")
            return True
        except Exception as e:
            self.logger.warning(f"Error writing to cache for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled:
            return False
            
        cache_path = self._get_cache_path(key)
        return os.path.exists(cache_path)
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    
            self.logger.info("Cache cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            File path for the cache key
        """
        # Create a safe filename from the key
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return os.path.join(self.cache_dir, f"{safe_key}.pkl")
    
    def _remove_file(self, path: str) -> None:
        """
        Remove a file if it exists.
        
        Args:
            path: File path to remove
        """
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            self.logger.warning(f"Error removing file {path}: {e}")