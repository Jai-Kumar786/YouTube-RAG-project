import pytest
from src.ingest import extract_video_id

def test_extract_video_id_valid_formats():
    """Test extraction of video ID from various valid YouTube URL formats."""
    expected_id = "dQw4w9WgXcQ"
    urls = [
        f"https://www.youtube.com/watch?v={expected_id}",
        f"http://youtu.be/{expected_id}",
        f"https://www.youtube.com/embed/{expected_id}",
        f"/v/{expected_id}",
        f"v={expected_id}",
        expected_id
    ]

    for url in urls:
        assert extract_video_id(url) == expected_id

def test_extract_video_id_invalid_formats():
    """Test that invalid formats raise ValueError."""
    invalid_urls = [
        "https://www.google.com",
        "dQw4w9WgXc",  # Too short
        "dQw4w9WgXcQQ", # Too long
        "",
        "   "
    ]

    for url in invalid_urls:
        with pytest.raises(ValueError):
            extract_video_id(url)

if __name__ == "__main__":
    pytest.main([__file__])
