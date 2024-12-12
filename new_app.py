from fastapi import FastAPI, HTTPException, Query
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from typing import Optional
import re
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YouTube Transcript API",
    description="API to fetch transcripts from YouTube videos",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic models for response structure
class TranscriptEntry(BaseModel):
    timestamp: str
    text: str
    start: float
    duration: float

class TranscriptResponse(BaseModel):
    video_id: str
    transcript: list[TranscriptEntry]

class LanguageInfo(BaseModel):
    language_code: str
    language_name: str

class LanguagesResponse(BaseModel):
    video_id: str
    available_languages: list[LanguageInfo]

def get_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from various forms of YouTube URLs.
    Returns None if the URL is invalid.
    """
    if not url:
        return None
        
    # Handle direct video ID input
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
        
    try:
        # Clean the URL
        url = url.strip()
        
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Handle different URL formats
        if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path[1:]
            
        if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
            if parsed_url.path == '/watch':
                # Regular watch URL
                query_params = parse_qs(parsed_url.query)
                return query_params.get('v', [None])[0]
            elif parsed_url.path.startswith(('/embed/', '/v/')):
                # Embedded or direct video URLs
                return parsed_url.path.split('/')[2]
                
        return None
        
    except Exception:
        return None

def format_transcript(transcript: list) -> list[TranscriptEntry]:
    """
    Format transcript entries into readable text with timestamps.
    """
    formatted_entries = []
    for entry in transcript:
        timestamp = int(entry['start'])
        minutes = timestamp // 60
        seconds = timestamp % 60
        time_str = f"[{minutes:02d}:{seconds:02d}]"
        formatted_entries.append(TranscriptEntry(
            timestamp=time_str,
            text=entry['text'],
            start=entry['start'],
            duration=entry.get('duration', 0)
        ))
    return formatted_entries

@app.get("/")
async def root():
    """
    Root endpoint showing API information
    """
    return {
        "message": "Welcome to YouTube Transcript API",
        "endpoints": {
            "/transcript": "GET - Fetch transcript (params: url, language)",
            "/languages": "GET - Get available languages (params: url)"
        }
    }

@app.get("/transcript", response_model=TranscriptResponse)
async def get_transcript(
    url: str = Query(..., description="YouTube URL or video ID"),
    language: Optional[str] = Query(None, description="Language code (e.g., 'en')")
):
    """
    Get transcript for a YouTube video
    """
    video_id = get_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or video ID")

    try:
        if language:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        else:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

        formatted_transcript = format_transcript(transcript)
        
        return TranscriptResponse(
            video_id=video_id,
            transcript=formatted_transcript
        )

    except Exception as e:
        error_message = str(e)
        if "Unable to find a transcript" in error_message:
            raise HTTPException(status_code=404, detail="No transcript available for this video")
        else:
            raise HTTPException(status_code=500, detail=f"Error fetching transcript: {error_message}")

@app.get("/languages", response_model=LanguagesResponse)
async def get_available_languages(
    url: str = Query(..., description="YouTube URL or video ID")
):
    """
    Get available transcript languages for a YouTube video
    """
    video_id = get_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or video ID")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available_languages = [
            LanguageInfo(
                language_code=t.language_code,
                language_name=t.language.title()
            )
            for t in transcript_list._manually_created_transcripts.values()
        ]

        return LanguagesResponse(
            video_id=video_id,
            available_languages=available_languages
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching available languages: {str(e)}"
        )
