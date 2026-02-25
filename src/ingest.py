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
        # 1. Initialize the modern API object 
        api = YouTubeTranscriptApi()
        
        # 2. Fetch the list of transcripts 
        transcript_list = api.list(video_id)
        
        # 3. Find the English transcript (this safely falls back to auto-generated)
        transcript = transcript_list.find_transcript(['en'])
        
        # 4. Fetch the actual text segments
        segments = transcript.fetch()
        
        # 5. Join all text segments using the updated object attribute (.text)
        transcript_text = " ".join([seg.text for seg in segments])
        
        # Clean up the text (optional but recommended for RAG)
        import re
        transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
        
        return transcript_text
        
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"Transcript unavailable for video {video_id}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None