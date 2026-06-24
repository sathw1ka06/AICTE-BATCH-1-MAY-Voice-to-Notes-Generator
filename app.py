from pathlib import Path

import streamlit as st

# Page config must be the first Streamlit call
st.set_page_config(
    page_title="EduScribe AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
_css_path = Path(__file__).parent / "assets" / "styles.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)

# Initialize database
from services.database_service import initialize_database
initialize_database()

# Session state defaults
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "viewing_lecture_id" not in st.session_state:
    st.session_state.viewing_lecture_id = None
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None

# Navigation
_NAV = [
    ("dashboard", "Dashboard",       "📊"),
    ("upload",    "Upload Lecture",  "📤"),
    ("library",   "Lecture Library", "📚"),
]

with st.sidebar:
    st.markdown(
        """<div class="sidebar-brand">
             <div class="sidebar-logo">EduScribe AI</div>
             <div class="sidebar-tagline">Voice to Notes Generator</div>
           </div>""",
        unsafe_allow_html=True,
    )

    for page_key, label, icon in _NAV:
        is_active = st.session_state.page == page_key
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{page_key}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.page = page_key
            st.session_state.viewing_lecture_id = None
            st.session_state.confirm_delete_id = None
            st.rerun()

    st.markdown(
        '<div class="sidebar-footer">Powered by Whisper &amp; Gemini 2.5 Flash</div>',
        unsafe_allow_html=True,
    )

# Page routing
_page = st.session_state.page

if _page == "dashboard":
    from pages.dashboard import render
    render()
elif _page == "upload":
    from pages.upload import render
    render()
elif _page == "library":
    from pages.library import render
    render()
