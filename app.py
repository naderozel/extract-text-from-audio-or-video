import streamlit as st
from groq import Groq
import tempfile, os, re, subprocess, json


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

          
st.markdown(" ---")
st.markdown("youtube video")
st.caption("You can also extract text from a YouTube video by providing the video URL below.")
yt_url = st.text_input("Enter YouTube video URL", placeholder="https://www.youtube.com/watch?v=example")



def parse_json3_sub(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        lines = []
        for event in data.get("events", []):
            for seg in event.get("segs", []):
                word = seg.get("utf8", "").strip()
                if word and word != "\n":
                    lines.append(word)
        full_text = " ".join(lines)
        return re.sub(r"\s+", " ", full_text).strip()


def get_yt_transcript(url):
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, "subs")
    for lang in ["ar", "en",""]:
        cmd = [
            "yt-dlp",
            "--no-playslist",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-format", "json3",
            "-o", output_path,


        ]
        if lang:
            cmd += ["--sub-lang", lang]
        cmd.append(url)
        subprocess.run(cmd, capture_output=True, text=True)

        for f in os.listdir(tmp_dir):
            if f.endswith(".json3"):
                sub_path = os.path.join(tmp_dir, f)
                text = parse_json3_sub(sub_path)
                for file in os.listdir(tmp_dir):
                    try:
                        os.unlink(os.path.join(tmp_dir, file)) 
                    except :
                        pass
                if text.strip():
                    return text
    raise ValueError("No subtitles found for the provided YouTube URL.")

if st.button("extract text from youtube", key="yt btn"):
    transcript = None
    with st.spinner("Extracting text from YouTube video..."):
        try:
            transcript = get_yt_transcript(yt_url)
        except Exception as e:
            st.error(f"Error extracting text: {e}")

    if not transcript or len(transcript.strip()) < 5:
        st.error("No text was extracted from the YouTube video.")
    else:
        st.subheader("Extracted Text")
        st.write(transcript)
        st.download_button("Download Extracted Text", transcript, file_name="extracted_text.txt")
