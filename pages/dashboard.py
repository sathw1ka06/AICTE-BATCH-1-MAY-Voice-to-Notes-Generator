from datetime import datetime

import pandas as pd
import streamlit as st

from services.database_service import get_all_lectures, get_stats


def render():
    st.title("Dashboard")
    st.caption("Overview of your lecture processing activity")
    st.divider()

    stats = get_stats()
    lectures = get_all_lectures()

    # ---- Metrics (native Streamlit — no custom HTML) ----
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Lectures", stats.get("total_lectures", 0))
    col2.metric("Notes Generated", stats.get("total_lectures", 0))
    col3.metric("Flashcards Created", stats.get("total_flashcards", 0))
    col4.metric("Quiz Questions", stats.get("total_quiz_questions", 0))

    st.divider()

    # ---- Recent lectures table ----
    st.subheader("Recent Lectures")

    if not lectures:
        st.info("No lectures processed yet. Upload your first lecture to get started.")
        return

    rows = []
    for lec in lectures[:10]:
        raw_dt = lec.get("created_at", "")
        try:
            dt_str = datetime.fromisoformat(raw_dt).strftime("%b %d, %Y")
        except Exception:
            dt_str = raw_dt[:10] if raw_dt else "—"

        rows.append(
            {
                "Lecture Name": lec.get("title") or "Untitled",
                "Upload Date": dt_str,
                "Status": "Processed",
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
