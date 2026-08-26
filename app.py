import streamlit as st
from groq import Groq
import tempfile, os, re, subprocess, json, shutil

st.set_page_config(page_title="Transcriber", page_icon="🎙️")
st.title("🎙️ Extract Text from Audio, Video & YouTube")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def transcribe_audio_file(path):
    with open(path, "rb") as f:
        return client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(os.path.basename(path), f),
            response_format="text"
        )

def extract_audio_from_video(video_path):
    audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio_path = audio_file.name
    audio_file.close()
    command = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        raise RuntimeError("FFmpeg error: " + result.stderr[-1000:])
    return audio_path

def parse_json3_sub(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    lines = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            word = seg.get("utf8", "").strip()
            if word and word != "\n":
                lines.append(word)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()

def get_yt_transcript(url):
    tmp_dir = tempfile.mkdtemp()
    try:
        output_path = os.path.join(tmp_dir, "subs")
        for lang in ["ar", "en", None]:
            command = [
                "yt-dlp", "--no-playlist", "--skip-download",
                "--write-subs", "--write-auto-subs",
                "--sub-format", "json3", "-o", output_path
            ]
            if lang:
                command += ["--sub-lang", lang]
            command.append(url)
            subprocess.run(command, capture_output=True, text=True)
            for filename in os.listdir(tmp_dir):
                if filename.endswith(".json3"):
                    text = parse_json3_sub(os.path.join(tmp_dir, filename))
                    if text:
                        return text
        raise ValueError("No subtitles found for this YouTube video.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

# Audio / Video
st.header("📁 Audio / Video")
uploaded_file = st.file_uploader(
    "Upload your file",
    type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "avi", "mov", "mkv"]
)

if uploaded_file:
    file_size_mb = uploaded_file.size / 1024**2
    if file_size_mb > 25:
        st.error("File size exceeds 25MB. Please upload a smaller file.")
    elif st.button("🎙️ Extract Text", key="file_btn"):
        temp_file_path = None
        audio_path = None
        try:
            with st.spinner("Extracting text..."):
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_file.write(uploaded_file.getbuffer())
                    temp_file_path = temp_file.name
                audio_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
                if ext in audio_extensions:
                    audio_path = temp_file_path
                else:
                    audio_path = extract_audio_from_video(temp_file_path)
                transcript = transcribe_audio_file(audio_path)
            if not transcript or len(transcript.strip()) < 5:
                st.error("No text was extracted.")
            else:
                st.subheader("📄 Extracted Text")
                st.text_area("Transcript", transcript, height=400)
                st.download_button(
                    "⬇️ Download Text",
                    transcript,
                    file_name="extracted_text.txt",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if audio_path and audio_path != temp_file_path and os.path.exists(audio_path):
                os.unlink(audio_path)

# YouTube
st.divider()
st.header("▶️ YouTube")
st.caption("Enter a YouTube URL to extract its subtitles.")
yt_url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=example"
)

def is_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+"
    return re.match(pattern, url.strip()) is not None

if st.button("🎬 Extract YouTube Text", key="yt_btn"):
    if not yt_url.strip():
        st.warning("Please enter a YouTube URL.")
    elif not is_youtube_url(yt_url):
        st.error("Please enter a valid YouTube URL.")
    else:
        with st.spinner("Extracting YouTube subtitles..."):
            try:
                transcript = get_yt_transcript(yt_url.strip())
                if not transcript or len(transcript.strip()) < 5:
                    st.error("No text was extracted from the YouTube video.")
                else:
                    st.subheader("📄 YouTube Transcript")
                    st.text_area("Transcript", transcript, height=400)
                    st.download_button(
                        "⬇️ Download Text",
                        transcript,
                        file_name="youtube_transcript.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
