"""In-memory PDF study guide generation using fpdf2."""
import io
import re
import unicodedata
from datetime import datetime

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Brand colours (RGB)
# ---------------------------------------------------------------------------
_DARK   = (1,   50,  55)    # #013237 — cover / headers
_ACCENT = (76,  167, 113)   # #4CA771 — dividers / highlights
_BODY   = (51,  51,  51)    # body text
_MUTED  = (100, 110, 115)   # captions / page header


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_pdf(lecture: dict) -> io.BytesIO:
    """Generate a study-guide PDF for *lecture* and return a BytesIO object."""
    pdf = _StudyGuidePDF()
    pdf.build(lecture)
    return io.BytesIO(bytes(pdf.output()))


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _safe(text: str) -> str:
    """Normalise Unicode and encode to Latin-1, replacing unsupported chars."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    return text.encode("latin-1", errors="replace").decode("latin-1")


_INLINE_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`")


def _strip_inline(s: str) -> str:
    return _INLINE_RE.sub(
        lambda m: m.group(1) or m.group(2) or m.group(3), s
    )


def _md_segments(text: str):
    """Yield (style, content) pairs for a Markdown string.

    Styles: h1 | h2 | h3 | bullet | body | blank
    """
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            yield "blank", ""
        elif s.startswith("### "):
            yield "h3", _strip_inline(s[4:])
        elif s.startswith("## "):
            yield "h2", _strip_inline(s[3:])
        elif s.startswith("# "):
            yield "h1", _strip_inline(s[2:])
        elif re.match(r"^[-*+] ", s):
            yield "bullet", _strip_inline(s[2:])
        else:
            yield "body", _strip_inline(s)


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------

class _StudyGuidePDF(FPDF):
    """Custom FPDF subclass with branded header / footer."""

    _title: str = ""

    # ---- Automatic page header (skipped on cover) ----

    def header(self):
        if self.page_no() <= 1:
            return
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*_MUTED)
        self.cell(0, 5, _safe(self._title), align="L")
        self.ln(2)
        self.set_draw_color(*_ACCENT)
        self.set_line_width(0.25)
        self.line(self.l_margin, self.get_y(),
                  self.w - self.r_margin, self.get_y())
        self.ln(5)

    # ---- Automatic page footer ----

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*_MUTED)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    # ---- Entry point ----

    def build(self, lecture: dict):
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(20, 20, 20)
        self._title = lecture.get("title") or "Untitled Lecture"

        self._cover(lecture)

        transcript = lecture.get("transcript") or ""
        notes      = lecture.get("notes")      or ""
        flashcards = lecture.get("flashcards") or []
        quiz       = lecture.get("quiz")       or []

        if transcript:
            self._new_section("TRANSCRIPT",
                              self._render_transcript, transcript)
        if notes:
            self._new_section("STUDY NOTES",
                              self._render_notes, notes)
        if flashcards:
            self._new_section(f"FLASHCARDS  ({len(flashcards)} cards)",
                              self._render_flashcards, flashcards)
        if quiz:
            self._new_section(f"QUIZ  ({len(quiz)} questions)",
                              self._render_quiz, quiz)

    # =========================================================================
    # Cover page
    # =========================================================================

    def _cover(self, lecture: dict):
        self.add_page()

        # Top dark band
        self.set_fill_color(*_DARK)
        self.rect(0, 0, self.w, 9, "F")

        self.set_y(48)

        # App name
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*_DARK)
        self.cell(0, 14, "EduScribe AI", align="C", ln=True)

        # Subtitle
        self.set_font("Helvetica", "", 13)
        self.set_text_color(*_MUTED)
        self.cell(0, 8, "Lecture Study Guide", align="C", ln=True)

        self.ln(14)

        # Accent divider
        cx = self.w / 2
        self.set_draw_color(*_ACCENT)
        self.set_line_width(1.2)
        self.line(cx - 32, self.get_y(), cx + 32, self.get_y())
        self.ln(14)

        # Lecture title
        self.set_font("Helvetica", "B", 17)
        self.set_text_color(*_DARK)
        self.multi_cell(0, 9, _safe(self._title), align="C")
        self.ln(10)

        # Metadata
        raw_dt = lecture.get("created_at", "")
        try:
            date_str = datetime.fromisoformat(raw_dt).strftime("%B %d, %Y")
        except Exception:
            date_str = str(raw_dt)[:10] if raw_dt else ""

        topic      = _safe(lecture.get("topic") or "")
        word_count = lecture.get("word_count") or 0

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*_MUTED)
        if date_str:
            self.cell(0, 6, f"Created: {date_str}", align="C", ln=True)
        if topic:
            self.cell(0, 6, f"Topic: {topic}", align="C", ln=True)
        if word_count:
            self.cell(0, 6, f"Words: {word_count:,}", align="C", ln=True)

        # Contents list
        self.ln(18)
        self.set_draw_color(*_MUTED)
        self.set_line_width(0.3)
        self.line(50, self.get_y(), self.w - 50, self.get_y())
        self.ln(10)

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_MUTED)
        self.cell(0, 6, "CONTENTS", align="C", ln=True)
        self.ln(4)

        flashcards = lecture.get("flashcards") or []
        quiz       = lecture.get("quiz")       or []
        for item in [
            "Transcript",
            "Study Notes",
            f"Flashcards  ({len(flashcards)} cards)",
            f"Quiz  ({len(quiz)} questions)",
        ]:
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*_BODY)
            self.cell(0, 6, f"  \xb7  {item}", align="C", ln=True)

        # Bottom accent band (absolute — always at page bottom)
        self.set_fill_color(*_ACCENT)
        self.rect(0, self.h - 9, self.w, 9, "F")

    # =========================================================================
    # Section helpers
    # =========================================================================

    def _new_section(self, heading: str, renderer, data):
        self.add_page()
        self._section_header(heading)
        renderer(data)

    def _section_header(self, title: str):
        self.set_fill_color(*_DARK)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, f"  {_safe(title)}", fill=True, ln=True)
        self.ln(6)
        self.set_text_color(*_BODY)

    # =========================================================================
    # Transcript
    # =========================================================================

    def _render_transcript(self, transcript: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_BODY)
        self.multi_cell(0, 5, _safe(transcript))

    # =========================================================================
    # Notes (Markdown → PDF)
    # =========================================================================

    def _render_notes(self, notes: str):
        for style, text in _md_segments(notes):
            text = _safe(text)

            if style == "blank":
                self.ln(2)

            elif style == "h1":
                self.ln(3)
                self.set_font("Helvetica", "B", 12)
                self.set_text_color(*_DARK)
                self.multi_cell(0, 6.5, text)
                y = self.get_y()
                self.set_draw_color(*_ACCENT)
                self.set_line_width(0.4)
                self.line(self.l_margin, y, self.w - self.r_margin, y)
                self.ln(4)

            elif style == "h2":
                self.ln(2)
                self.set_font("Helvetica", "B", 10.5)
                self.set_text_color(*_DARK)
                self.multi_cell(0, 6, text)
                self.ln(1)

            elif style == "h3":
                self.set_font("Helvetica", "B", 9.5)
                self.set_text_color(*_BODY)
                self.multi_cell(0, 5.5, text)

            elif style == "bullet":
                old_lm = self.l_margin
                self.set_left_margin(26)
                self.set_x(26)
                self.set_font("Helvetica", "", 9.5)
                self.set_text_color(*_BODY)
                self.multi_cell(0, 5, f"\xb7  {text}")
                self.set_left_margin(old_lm)

            else:  # body
                self.set_font("Helvetica", "", 9.5)
                self.set_text_color(*_BODY)
                self.multi_cell(0, 5, text)

    # =========================================================================
    # Flashcards
    # =========================================================================

    def _render_flashcards(self, flashcards: list):
        for i, card in enumerate(flashcards, 1):
            q = _safe(card.get("question") or "")
            a = _safe(card.get("answer")   or "")

            # Card label
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*_ACCENT)
            self.cell(0, 5, f"Card {i}", ln=True)

            old_lm = self.l_margin
            self.set_left_margin(26)

            # Question
            self.set_x(26)
            self.set_font("Helvetica", "B", 9.5)
            self.set_text_color(*_DARK)
            self.multi_cell(0, 5, f"Q: {q}")

            # Answer
            self.set_x(26)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*_BODY)
            self.multi_cell(0, 5, f"A: {a}")

            self.set_left_margin(old_lm)
            self.ln(3)

            self.set_draw_color(210, 215, 210)
            self.set_line_width(0.2)
            self.line(self.l_margin, self.get_y(),
                      self.w - self.r_margin, self.get_y())
            self.ln(4)

    # =========================================================================
    # Quiz
    # =========================================================================

    def _render_quiz(self, quiz: list):
        for i, q in enumerate(quiz, 1):
            question    = _safe(q.get("question")    or "")
            correct     = q.get("correct")            or ""
            explanation = _safe(q.get("explanation") or "")

            # Question
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*_DARK)
            self.multi_cell(0, 5.5, f"Q{i}.  {question}")
            self.ln(2)

            # Options
            old_lm = self.l_margin
            self.set_left_margin(28)
            for opt in q.get("options") or []:
                opt_text = _safe(opt)
                letter   = opt_text[0] if opt_text else ""
                self.set_x(28)
                if letter == correct:
                    self.set_font("Helvetica", "B", 9.5)
                    self.set_text_color(*_ACCENT)
                    self.multi_cell(0, 5, f"{opt_text}  (Correct)")
                else:
                    self.set_font("Helvetica", "", 9.5)
                    self.set_text_color(*_BODY)
                    self.multi_cell(0, 5, opt_text)

            # Explanation
            if explanation:
                self.ln(1)
                self.set_x(28)
                self.set_font("Helvetica", "I", 8.5)
                self.set_text_color(*_MUTED)
                self.multi_cell(0, 4.5, f"Explanation: {explanation}")

            self.set_left_margin(old_lm)
            self.ln(4)
            self.set_draw_color(210, 215, 210)
            self.set_line_width(0.2)
            self.line(self.l_margin, self.get_y(),
                      self.w - self.r_margin, self.get_y())
            self.ln(4)
