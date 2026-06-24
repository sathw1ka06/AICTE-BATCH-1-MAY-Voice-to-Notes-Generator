import time

import streamlit as st

from services.database_service import save_lecture
from services.gemini_service import generate_all_content
from services.whisper_service import transcribe_audio

SUPPORTED_FORMATS = ["mp3", "wav", "m4a"]
MAX_SIZE_MB = 50
WARN_SIZE_MB = 30


def render():
    st.title("Upload Lecture")
    st.caption("Upload lecture audio to generate transcripts, notes, flashcards, and quizzes.")
    st.divider()

    # ---- Form ----
    lecture_title = st.text_input(
        "Lecture Title",
        placeholder="e.g., Introduction to Neural Networks — Week 4",
    )

    uploaded_file = st.file_uploader(
        "Audio File",
        type=SUPPORTED_FORMATS,
        help="Supported formats: MP3, WAV, M4A · Maximum 50 MB",
    )

    if uploaded_file is None:
        return

    audio_bytes = uploaded_file.getvalue()
    file_size_mb = len(audio_bytes) / (1024 * 1024)

    if file_size_mb > MAX_SIZE_MB:
        st.error(
            f"File size ({file_size_mb:.1f} MB) exceeds the 50 MB limit. "
            "Please compress your audio and try again."
        )
        return

    if file_size_mb > WARN_SIZE_MB:
        st.warning(
            f"Large file ({file_size_mb:.1f} MB) detected. "
            "Processing may take several minutes. Files under 25 minutes are recommended."
        )

    file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    effective_title = lecture_title.strip() or uploaded_file.name.rsplit(".", 1)[0]

    st.caption(f"File: **{uploaded_file.name}** · {file_size_mb:.1f} MB · {file_ext.upper()}")

    if not st.button("Generate Study Materials", type="primary", use_container_width=True):
        return

    # ---- Processing ----
    progress_bar = st.progress(0, text="Starting…")
    status_text = st.empty()

    try:
        # Step 1 — Whisper
        progress_bar.progress(15, text="Transcribing audio with Whisper Base…")
        whisper_result = transcribe_audio(audio_bytes, file_ext)
        transcript: str = whisper_result["transcript"]
        duration: float = whisper_result["duration"]
        word_count: int = whisper_result["word_count"]
        whisper_time: float = whisper_result["processing_time"]

        if not transcript:
            st.error(
                "Transcription returned empty output. "
                "The audio may be silent, corrupted, or in an unsupported format."
            )
            return

        # Step 2 — Gemini (single API call)
        progress_bar.progress(40, text="Generating study materials with Gemini 2.5 Flash…")
        ai = generate_all_content(transcript)

        notes = ai.get("notes", "")
        flashcards = ai.get("flashcards", [])
        quiz = ai.get("quiz", [])
        topic = ai.get("topic", "General")
        keywords = ai.get("keywords", [])

        # Step 3 — Save
        progress_bar.progress(90, text="Saving to database…")
        lecture_id = save_lecture(
            title=effective_title,
            audio_blob=audio_bytes,
            duration=duration,
            transcript=transcript,
            summary="",
            notes=notes,
            flashcards=flashcards,
            quiz=quiz,
            topic=topic,
            keywords=keywords,
            word_count=word_count,
            processing_time=whisper_time,
        )

        progress_bar.progress(100, text="Complete!")
        status_text.empty()

    except RuntimeError as exc:
        progress_bar.empty()
        st.error(str(exc))
        st.info(
            "If you are on the Gemini free tier, wait a minute and try again. "
            "The app retried 5 times with exponential backoff before giving up."
        )
        return
    except Exception as exc:
        progress_bar.empty()
        st.error(f"Unexpected error: {exc}")
        return

    # ---- Success checklist ----
    st.success(f"**'{effective_title}'** processed successfully!")

    r1, r2 = st.columns(2)
    r1.success(f"✓ Transcript generated ({word_count:,} words)")
    r1.success("✓ Study Notes generated")
    r2.success(f"✓ {len(flashcards)} Flashcards generated")
    r2.success(f"✓ {len(quiz)} Quiz Questions generated")

    st.info("Redirecting to Lecture Library…")
    time.sleep(1.2)
    st.session_state.page = "library"
    st.session_state.viewing_lecture_id = lecture_id
    st.rerun()
