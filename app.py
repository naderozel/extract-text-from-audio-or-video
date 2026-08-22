import streamlit as st
from groq import Groq
import tempfile
import os


st.title("Extract Text from Audio or Video")

# Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.write("Upload your audio or video file below")

uploaded_file = st.file_uploader(
    "Upload your file",
    type=["mp3", "wav", "mp4", "mpeg", "mpga", "m4a", "ogg", "webm"]
)


def transcribe_audio_file(path):

    with open(path, "rb") as f:

        transcript = client.audio.transcriptions.create(
            file=(os.path.basename(path), f.read()),
            model="whisper-large-v3",
            response_format="json"
        )

    return transcript.text


if uploaded_file:

    # Groq free tier limit is 25 MB
    if uploaded_file.size / 1024**2 > 25:

        st.error(
            "File size exceeds 25MB. Please upload a smaller file."
        )

    elif st.button("Extract Text", key="file_btn"):

        with st.spinner("Extracting text from audio/video..."):

            ext = os.path.splitext(uploaded_file.name)[-1].lower()

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ext
            ) as temp_file:

                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            try:

                transcript = transcribe_audio_file(temp_file_path)

            except Exception as e:

                st.error(f"Transcription failed: {e}")
                transcript = ""

            finally:

                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        if not transcript or len(transcript.strip()) < 5:

            st.error(
                "No text was extracted from the audio/video file."
            )

        else:

            st.subheader("Extracted Text")

            st.write(transcript)

            st.download_button(
                "Download Extracted Text",
                transcript,
                file_name="extracted_text.txt",
                mime="text/plain"
            )


st.markdown("---")
