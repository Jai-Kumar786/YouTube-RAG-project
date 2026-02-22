"""
Transcript ingestion — fetches plain-text transcript from a YouTube URL.
"""
from __future__ import annotations

import re
from youtube_transcript_api import YouTubeTranscriptApi


# Compile regex patterns once at module level
VIDEO_ID_PATTERNS = [
    re.compile(r"(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"^([a-zA-Z0-9_-]{11})$"),  # bare video ID
]


def extract_video_id(url: str) -> str:
    """Extract the 11-char video ID from various YouTube URL formats."""
    for pattern in VIDEO_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")




from youtube_transcript_api import YouTubeTranscriptApi

def fetch_transcript(youtube_url: str) -> tuple[str, list]:
    """
    Fetch the transcript for the given YouTube video URL.
    Returns the full transcript as a single string and the list of segments.
    """
    video_id = extract_video_id(youtube_url)
    try:
        # 1. Initialize the API object
        api = YouTubeTranscriptApi()

        # 2. Fetch the list of transcripts using .list()
        transcript_list = api.list(video_id)

        # 3. Find the English transcript (falls back to auto-generated)
        transcript = transcript_list.find_transcript(['en'])

        # 4. Fetch the actual text segments
        segments = transcript.fetch()

        # 5. Join all text segments using the updated object attribute (.text)
        full_text = " ".join(seg.text for seg in segments)

        # Optional: Clean up extra spaces/newlines that auto-generated subs often have
        import re
        full_text = re.sub(r'\s+', ' ', full_text)

        return full_text.strip(), segments

    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript for video {video_id}: {e}") from e
