import re
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

    if dur_min >= 0.1:
        st.caption(f"{word_count:,} words  ·  {dur_min:.1f} min")
    else:
        st.caption(f"{word_count:,} words")

    st.divider()

    # --- PDF download ---
    try:
        from services.pdf_service import generate_lecture_pdf
        pdf_bytes = generate_lecture_pdf(lecture)
        safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"{safe_title or 'lecture'}.pdf",
            mime="application/pdf",
        )
    except Exception as exc:
        st.error(f"PDF generation failed: {exc}")

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


# ===========================================================================
# Flashcards — card-by-card learn → test → feedback flow
# ===========================================================================

def _flashcards_tab(lecture: dict):
    flashcards = lecture.get("flashcards") or []
    if not flashcards:
        st.info("No flashcards available for this lecture.")
        return

    lec_id = lecture["id"]
    sk = f"fc_{lec_id}"
    if sk not in st.session_state:
        st.session_state[sk] = {
            "card_idx": 0,       # current card (0-based)
            "phase": "learn",    # "learn" | "testing" | "evaluated"
            "eval_result": None,
            "results": [],       # "correct" | "partial" | "incorrect" per card
            "done": False,
        }
    s = st.session_state[sk]

    if s["done"]:
        _fc_summary(s)
        return

    n = len(flashcards)
    idx = s["card_idx"]
    card = flashcards[idx]
    phase = s["phase"]

    phase_labels = {"learn": "Study", "testing": "Testing", "evaluated": "Result"}
    st.caption(f"Card {idx + 1} of {n}  ·  {phase_labels[phase]}")
    st.markdown("")

    # Question — always visible
    with st.container(border=True):
        st.markdown("**Question:**")
        st.markdown(card.get("question", ""))

    st.markdown("")

    # ---- Learn phase: show answer + Test Myself ----
    if phase == "learn":
        with st.container(border=True):
            st.markdown("**Answer:**")
            st.markdown(card.get("answer", ""))

        st.markdown("")
        if st.button("Test Myself", type="primary", use_container_width=True):
            s["phase"] = "testing"
            st.rerun()

    # ---- Testing phase: text input + Check Answer ----
    elif phase == "testing":
        answer_key = f"fc_ans_{lec_id}_{idx}"
        student_answer = st.text_area(
            "Type your answer from memory:",
            key=answer_key,
            height=120,
            placeholder="Write your answer from memory…",
        )
        if st.button(
            "Check Answer",
            type="primary",
            disabled=not (student_answer or "").strip(),
        ):
            from services.gemini_service import evaluate_flashcard_answer
            with st.spinner("Evaluating your answer…"):
                eval_result = evaluate_flashcard_answer(
                    question=card.get("question", ""),
                    expected_answer=card.get("answer", ""),
                    student_answer=student_answer.strip(),
                )
            s["eval_result"] = eval_result
            s["phase"] = "evaluated"
            st.rerun()

    # ---- Evaluated phase: show result + Next / Finish ----
    else:
        result = s["eval_result"] or {}
        result_label = result.get("result", "❌ Incorrect")
        feedback = result.get("feedback", "")
        expected = result.get("expected") or card.get("answer", "")

        if "✅" in result_label:
            st.success(f"**{result_label}**")
        elif "⚠️" in result_label:
            st.warning(f"**{result_label}**")
        else:
            st.error(f"**{result_label}**")

        if feedback:
            st.markdown(f"**Feedback:** {feedback}")

        # Always show expected answer when not fully correct
        if "✅" not in result_label:
            with st.expander("Expected Answer", expanded=True):
                st.markdown(expected)

        st.markdown("")

        def _record():
            if "✅" in result_label:
                s["results"].append("correct")
            elif "⚠️" in result_label:
                s["results"].append("partial")
            else:
                s["results"].append("incorrect")

        if idx < n - 1:
            if st.button("Next Flashcard →", type="primary", use_container_width=True):
                _record()
                s["card_idx"] += 1
                s["phase"] = "learn"
                s["eval_result"] = None
                st.rerun()
        else:
            if st.button("See My Results", type="primary", use_container_width=True):
                _record()
                s["done"] = True
                st.rerun()


def _fc_summary(s: dict):
    results = s.get("results", [])
    n = len(results)
    correct = results.count("correct")
    partial = results.count("partial")
    incorrect = results.count("incorrect")
    accuracy = int((correct + partial * 0.5) / n * 100) if n > 0 else 0

    st.markdown("### Flashcard Session Complete")
    st.markdown("")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", n)
    c2.metric("✅ Correct", correct)
    c3.metric("⚠️ Partially Correct", partial)
    c4.metric("❌ Incorrect", incorrect)
    st.metric("Accuracy", f"{accuracy}%")

    st.markdown("")
    if st.button("Restart Flashcards", use_container_width=True):
        s.update({
            "card_idx": 0,
            "phase": "learn",
            "eval_result": None,
            "results": [],
            "done": False,
        })
        st.rerun()


# ===========================================================================
# Quiz — interactive per-question submission with score tracking
# ===========================================================================

def _quiz_tab(lecture: dict):
    quiz = lecture.get("quiz") or []
    if not quiz:
        st.info("No quiz available for this lecture.")
        return

    lec_id = lecture["id"]
    sk = f"quiz_{lec_id}"
    if sk not in st.session_state:
        st.session_state[sk] = {"submitted": {}, "score": 0}
    s = st.session_state[sk]

    answered = sum(1 for v in s["submitted"].values() if v)
    st.caption(f"{answered}/{len(quiz)} answered")
    st.markdown("")

    for i, q in enumerate(quiz):
        question_text = q.get("question") or ""
        correct = q.get("correct") or ""
        options = q.get("options") or []
        explanation = q.get("explanation") or ""
        radio_key = f"quiz_r_{lec_id}_{i}"

        with st.container(border=True):
            st.markdown(f"**Q{i + 1}. {question_text}**")
            st.markdown("")

            if s["submitted"].get(i):
                # Answered — show result with highlighting
                selected = st.session_state.get(radio_key) or ""
                sel_letter = selected[0] if selected else ""

                for opt in options:
                    letter = opt[0] if opt else ""
                    if letter == correct:
                        st.markdown(f"✅ **{opt}**")
                    elif letter == sel_letter:
                        st.markdown(f"❌ {opt}")
                    else:
                        st.markdown(f"◻ {opt}")

                if explanation:
                    st.info(f"💡 {explanation}")
            else:
                # Interactive — radio + submit button
                selected = st.radio(
                    "options",
                    options=options,
                    key=radio_key,
                    label_visibility="collapsed",
                    index=None,
                )
                if st.button(
                    "Submit Answer",
                    key=f"quiz_sub_{lec_id}_{i}",
                    disabled=(selected is None),
                ):
                    s["submitted"][i] = True
                    if (selected or "")[0:1] == correct:
                        s["score"] += 1
                    st.rerun()

    # Final score summary after all questions answered
    if answered == len(quiz):
        st.divider()
        score = s["score"]
        pct = int(score / len(quiz) * 100)

        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{score}/{len(quiz)}")
        c2.metric("Correct", score)
        c3.metric("Accuracy", f"{pct}%")

        if st.button("Retake Quiz", key=f"quiz_retake_{lec_id}"):
            del st.session_state[sk]
            for j in range(len(quiz)):
                st.session_state.pop(f"quiz_r_{lec_id}_{j}", None)
            st.rerun()
