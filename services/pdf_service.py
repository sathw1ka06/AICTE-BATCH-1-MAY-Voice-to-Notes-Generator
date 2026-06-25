"""Lightweight PDF export using fpdf2 — transcript + notes only."""
import re
from datetime import datetime

from fpdf import FPDF


def _sanitize(text: str) -> str:
    """Replace Unicode characters unsupported by FPDF's built-in Latin-1 fonts."""
    if not text:
        return ""
    replacements = {
        "✓": "[ok]",   # check mark
        "✔": "[ok]",   # heavy check mark
        "❌": "[x]",    # cross mark
        "⚠": "[!]",    # warning sign
        "✅": "[ok]",   # white heavy check mark
        "•": "-",      # bullet
        "‣": "-",      # triangular bullet
        "◦": "-",      # white bullet
        "–": "-",      # en dash
        "—": "-",      # em dash
        "‘": "'",      # left single quotation mark
        "’": "'",      # right single quotation mark
        "“": '"',      # left double quotation mark
        "”": '"',      # right double quotation mark
        "…": "...",    # horizontal ellipsis
        " ": " ",      # non-breaking space
        "·": "-",      # middle dot
        "◻": "-",      # white medium square (used as bullet in some outputs)
        "◼": "-",      # black medium square
        "◽": "-",      # white medium small square
        "◾": "-",      # black medium small square
        "□": "-",      # white square
        "■": "-",      # black square
        "⯈": ">",      # black right-pointing pointer
        "➢": ">",      # three-d top-lighted rightwards arrowhead
    }
    for char, sub in replacements.items():
        text = text.replace(char, sub)
    # Strip markdown bold/italic markers and headings so they render as plain text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_{1,2}(.+?)_{1,2}", r"\1", text)
    text = re.sub(r"^#{1,6} ", "", text, flags=re.MULTILINE)
    # Drop any remaining characters outside Latin-1
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


def generate_lecture_pdf(lecture: dict) -> bytes:
    """Return PDF bytes containing only the transcript and study notes."""
    title = lecture.get("title") or "Untitled"
    created_at = lecture.get("created_at") or ""
    transcript = lecture.get("transcript") or ""
    notes = lecture.get("notes") or ""

    try:
        date_str = datetime.fromisoformat(created_at).strftime("%B %d, %Y")
    except Exception:
        date_str = created_at[:10] if created_at else "Unknown date"

    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # App header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EduScribe AI", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Lecture Voice-to-Notes Generator", ln=True, align="C")
    pdf.ln(8)

    # Lecture title
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, _sanitize(title))
    pdf.ln(4)

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Generated On: {date_str}", ln=True)
    pdf.ln(6)

    # Transcript section
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "==========================", ln=True)
    pdf.cell(0, 7, "TRANSCRIPT", ln=True)
    pdf.cell(0, 7, "==========================", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _sanitize(transcript) or "No transcript available.")
    pdf.ln(10)

    # Study notes section
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "==========================", ln=True)
    pdf.cell(0, 7, "STUDY NOTES", ln=True)
    pdf.cell(0, 7, "==========================", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _sanitize(notes) or "No study notes available.")

    return bytes(pdf.output())
