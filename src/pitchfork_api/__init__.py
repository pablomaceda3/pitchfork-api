"""
Pitchfork API - A Python wrapper for Pitchfork music reviews with sentiment analysis.
"""

__version__ = "0.1.0"

from .client import PitchforkClient
from .models.review import Review
from .models.album import Album
from .sentiment import SentimentAnalyzer

__all__ = ["PitchforkClient", "Review", "Album", "SentimentAnalyzer"]

# Add CLI entrypoint
def main():
    from .cli import main as cli_main
    cli_main()