import time
import tempfile
from pathlib import Path

import streamlit as st
import whisper


@st.cache_resource(show_spinner=False)
def _load_model():
    return whisper.load_model("base")


def transcribe_audio(audio_bytes: bytes, file_extension: str = "mp3") -> dict:
    model = _load_model()

    with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        start = time.time()
        result = model.transcribe(tmp_path)
        elapsed = time.time() - start

        transcript = result.get("text", "").strip()
        duration = result.get("duration", 0.0)
        word_count = len(transcript.split()) if transcript else 0

        return {
            "transcript": transcript,
            "duration": float(duration),
            "word_count": word_count,
            "processing_time": elapsed,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)
