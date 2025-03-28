"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def ensure_fixtures_dir():
    """
    Ensures the fixtures directory exists.
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_data_dir():
    """
    Return the path to the test data directory.
    """
    return os.path.join(os.path.dirname(__file__), "fixtures")