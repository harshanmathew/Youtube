import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import re

def get_video_id(url):
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

def format_transcript(transcript):
    """
    Format transcript entries into readable text with timestamps.
    """
    formatted_text = []
    for entry in transcript:
        timestamp = int(entry['start'])
        minutes = timestamp // 60
        seconds = timestamp % 60
        time_str = f"[{minutes:02d}:{seconds:02d}]"
        formatted_text.append(f"{time_str} {entry['text']}")
    return "\n".join(formatted_text)

# Set up the Streamlit page configuration
st.set_page_config(
    page_title="YouTube Transcript Fetcher",
    page_icon="📝",
    layout="wide"
)

# Add CSS for better styling
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stTextArea > div > div > textarea {
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# Main app layout
st.title("📝 YouTube Transcript Fetcher")
st.markdown("Enter a YouTube video URL or ID to fetch its transcript.")

# Input for YouTube URL
url = st.text_input(
    "Enter YouTube URL or video ID",
    placeholder="https://www.youtube.com/watch?v=... or video ID"
)

# Add language selection (optional)
show_advanced = st.checkbox("Show advanced options")
selected_language = None

if show_advanced:
    try:
        if url and (video_id := get_video_id(url)):
            # Get available transcript languages
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_languages = [
                (t.language_code, t.language.title()) 
                for t in transcript_list._manually_created_transcripts.values()
            ]
            if available_languages:
                selected_language = st.selectbox(
                    "Select transcript language",
                    options=[code for code, _ in available_languages],
                    format_func=lambda x: dict(available_languages)[x]
                )
    except Exception:
        st.warning("Please enter a valid URL to see available languages.")

# Fetch transcript button
if st.button("Get Transcript", type="primary"):
    if not url:
        st.error("Please enter a YouTube URL or video ID.")
    else:
        video_id = get_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL or video ID. Please check and try again.")
        else:
            try:
                with st.spinner("Fetching transcript..."):
                    if selected_language:
                        transcript = YouTubeTranscriptApi.get_transcript(
                            video_id, 
                            languages=[selected_language]
                        )
                    else:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    
                    # Format and display the transcript
                    formatted_transcript = format_transcript(transcript)
                    
                    # Display video information
                    st.success("Transcript fetched successfully!")
                    
                    # Add copy button and display transcript
                    st.code(formatted_transcript, language="markdown")
                    
                    # Download button
                    st.download_button(
                        label="Download Transcript",
                        data=formatted_transcript,
                        file_name=f"transcript_{video_id}.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                error_message = str(e)
                if "Unable to find a transcript" in error_message:
                    st.error("No transcript available for this video. The video might not have closed captions.")
                else:
                    st.error(f"Error fetching transcript: {error_message}")

# Add footer with instructions
st.markdown("---")
st.markdown("""
### Supported URL formats:
- Regular: `https://www.youtube.com/watch?v=VIDEO_ID`
- Short: `https://youtu.be/VIDEO_ID`
- Embedded: `https://www.youtube.com/embed/VIDEO_ID`
- Direct video ID: `VIDEO_ID`
""")

