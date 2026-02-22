import urllib.parse as urlparse
from urllib.parse import parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def extract_video_id(url: str) -> str:
    """
    Extracts the video ID from various forms of YouTube URLs.
    """
    parsed_url = urlparse.urlparse(url)
    
    # Handle youtu.be/VIDEO_ID
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
        
    # Handle youtube.com/watch?v=VIDEO_ID
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            query_params = parse_qs(parsed_url.query)
            return query_params.get('v', [None])[0]
            
    return None

def fetch_youtube_transcript(video_id: str) -> str:
    """
    Fetches the transcript for a given YouTube video ID.
    Returns the full text as a single string, or None if it fails.
    """
    try:
        # Fetch the transcript (defaults to English)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine all the text dictionaries into one continuous string
        transcript_text = " ".join([entry['text'] for entry in transcript_list])
        return transcript_text
        
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"Transcript unavailable for video {video_id}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None