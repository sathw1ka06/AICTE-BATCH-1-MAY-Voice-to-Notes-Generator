from datetime import datetime

import streamlit as st

from services.database_service import delete_lecture, get_all_lectures, get_lecture_by_id


def render():
    st.title("Lecture Library")
    st.caption("Browse and review all processed lectures")
    st.divider()

    if "viewing_lecture_id" not in st.session_state:
        st.session_state.viewing_lecture_id = None
    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None

    lectures = get_all_lectures()

    if not lectures:
        st.info("Your library is empty. Upload your first lecture to get started.")
        return

    # Lecture detail view
    if st.session_state.viewing_lecture_id:
        if st.button("← Back to Library"):
            st.session_state.viewing_lecture_id = None
            st.rerun()
        _show_viewer(st.session_state.viewing_lecture_id)
        return

    # ---- Search bar ----
    query = st.text_input("Search lectures", placeholder="Search by title…")

    if query:
        q = query.lower()
        lectures = [lec for lec in lectures if q in (lec.get("title") or "").lower()]

    st.caption(f"{len(lectures)} lecture(s)")

    if not lectures:
        st.info("No lectures match your search.")
        return

    # ---- Lecture list ----
    for lec in lectures:
        lec_id = lec["id"]
        title = lec.get("title") or "Untitled"
        raw_dt = lec.get("created_at", "")
        try:
            date_str = datetime.fromisoformat(raw_dt).strftime("%b %d, %Y")
        except Exception:
            date_str = raw_dt[:10] if raw_dt else "—"

        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{title}**")
                st.caption(f"Uploaded {date_str}  ·  Status: Processed")
            with right:
                if st.button("View", key=f"view_{lec_id}", use_container_width=True):
                    st.session_state.viewing_lecture_id = lec_id
                    st.session_state.confirm_delete_id = None
                    st.rerun()

                if st.session_state.confirm_delete_id == lec_id:
                    if st.button(
                        "Confirm Delete",
                        key=f"confirm_{lec_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        delete_lecture(lec_id)
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                else:
                    if st.button("Delete", key=f"del_{lec_id}", use_container_width=True):
                        st.session_state.confirm_delete_id = lec_id
                        st.rerun()


# ---------------------------------------------------------------------------
# Lecture Viewer
# ---------------------------------------------------------------------------

def _show_viewer(lecture_id: int):
    lecture = get_lecture_by_id(lecture_id)
    if not lecture:
        st.error("Lecture not found.")
        st.session_state.viewing_lecture_id = None
        return

    title = lecture.get("title") or "Untitled"
    word_count = lecture.get("word_count") or 0
    duration = lecture.get("duration") or 0.0
    dur_min = duration / 60

    st.subheader(title)

    # Show duration only when Whisper returned a meaningful value
    if dur_min >= 0.1:
        st.caption(f"{word_count:,} words  ·  {dur_min:.1f} min")
    else:
        st.caption(f"{word_count:,} words")

    st.divider()

    tab_tr, tab_no, tab_fc, tab_qz = st.tabs(["Transcript", "Notes", "Flashcards", "Quiz"])

    with tab_tr:
        _transcript_tab(lecture)
    with tab_no:
        _notes_tab(lecture)
    with tab_fc:
        _flashcards_tab(lecture)
    with tab_qz:
        _quiz_tab(lecture)


def _transcript_tab(lecture: dict):
    transcript = lecture.get("transcript") or ""
    word_count = lecture.get("word_count") or 0

    st.metric("Word Count", f"{word_count:,}")

    if transcript:
        st.text_area(
            "Transcript",
            value=transcript,
            height=400,
            label_visibility="collapsed",
        )
    else:
        st.info("No transcript available for this lecture.")


def _notes_tab(lecture: dict):
    notes = lecture.get("notes") or ""
    if notes:
        st.markdown(notes)
    else:
        st.info("No study notes available for this lecture.")


def _flashcards_tab(lecture: dict):
    flashcards = lecture.get("flashcards") or []

    if not flashcards:
        st.info("No flashcards available for this lecture.")
        return

    st.caption(f"{len(flashcards)} flashcard(s)")

    for i, card in enumerate(flashcards, 1):
        question = card.get("question") or ""
        answer = card.get("answer") or ""
        label = f"Card {i}: {question[:70]}{'…' if len(question) > 70 else ''}"
        with st.expander(label):
            st.markdown(f"**Question:** {question}")
            st.divider()
            st.markdown(f"**Answer:** {answer}")


def _quiz_tab(lecture: dict):
    quiz = lecture.get("quiz") or []

    if not quiz:
        st.info("No quiz available for this lecture.")
        return

    st.caption(f"{len(quiz)} question(s)")

    for i, q in enumerate(quiz, 1):
        question = q.get("question") or ""
        correct = q.get("correct") or ""
        label = f"Q{i}: {question[:70]}{'…' if len(question) > 70 else ''}"

        with st.expander(label):
            st.markdown(f"**{question}**")
            st.markdown("")

            for opt in q.get("options") or []:
                if opt and opt[0] == correct:
                    st.markdown(f"**{opt} ✓**")
                else:
                    st.markdown(f"{opt}")

            if correct or q.get("explanation"):
                st.divider()
            if correct:
                st.markdown(f"**Correct Answer:** {correct}")
            if q.get("explanation"):
                st.markdown(f"*{q['explanation']}*")
