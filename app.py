import streamlit as st
from groq import Groq
import tempfile, os, re


st.title("extract text from audio or video")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.write("Upload your audio or video file below")
uploaded_file = st.file_uploader("Upload your file", type=["mp3", "wav", "mp4", "avi"])

def transcribe_audio_file(path):
    with open(path, "rb") as f:
        transcript = client.audio.transcribe(
            model="whisper-large-v3",
            file=(os.path.basename(path), f),
            response_format="text"        
        )
        return transcript

if uploaded_file :
    if uploaded_file.size / 1024**2 > 25:
        st.error("File size exceeds 25MB. Please upload a smaller file.")
    elif st.button("extract text", key="file btn"):
        with st.spinner("Extracting text from audio/video..."):
            ext = os.path.splitext(uploaded_file.name)[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            try:
                transcript = transcribe_audio_file(temp_file_path)
            finally:
                os.unlink(temp_file_path)    
        if not transcript or len(transcript.strip()) < 5:
            st.error("No text was extracted from the audio/video file.")
        else:
            st.subheader("Extracted Text")
            st.write(transcript)
            st.download_button("Download Extracted Text", transcript, file_name="extracted_text.txt")

st.markdown(" --- ")

