import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# Function to extract video ID from the URL
def get_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be':  # Short URLs
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':  # Regular URL
            return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/embed/':  # Embedded URLs
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':  # Older embedded URLs
            return query.path.split('/')[2]
    return None

# Streamlit app layout
st.title("YouTube Transcript Fetcher")

# Input for YouTube URL
url = st.text_input("Enter the YouTube video URL:")

# Fetch the transcript when the button is clicked
if st.button("Get Transcript"):
    video_id = get_video_id(url)

    # Fetch the transcript
    if video_id:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Combine all transcript entries into a single paragraph
            full_transcript = " ".join([entry['text'] for entry in transcript])
            st.text_area("Transcript", full_transcript, height=300)
        except Exception as e:
            st.error("Could not retrieve transcript: " + str(e))
    else:
        st.error("Invalid YouTube URL")
