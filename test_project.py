import pytest
from project import BASE_URL
from project import get_discogs_headers
from project import test_authentication

# Authentication Tests
def test_get_discogs_headers():
    """Test with pytest-env plugin configuration."""
    headers = get_discogs_headers()
    
    assert "Authorization" in headers
    assert "Discogs token=" in headers["Authorization"]
    assert headers["User-Agent"] == "DiMMS-CLI/1.0"

