import re
import time

import streamlit as st
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5  # 6 total attempts (first + 5 retries)

_PROMPT_TEMPLATE = """You are an expert academic content generator. From the lecture transcript below, produce ALL of the following in ONE response.

Use EXACTLY these section headers, each on its own line with a # prefix:

# NOTES
Write comprehensive study notes in Markdown format. Use:
  - # for main topic titles
  - ## for subtopics
  - ### for sub-subtopics
  - - bullets for key points
  - **bold** for key terms and definitions
  - *italic* for examples
Include: definitions, examples, key concepts, important takeaways, and exam revision points.

# FLASHCARDS
Generate 15 flashcards. Use EXACTLY this format with one blank line between cards:

Q: [question testing a key concept, definition, or process]
A: [clear, complete answer in 1-3 sentences]

Q: [next question]
A: [next answer]

# QUIZ
Generate 10 multiple-choice questions. Use EXACTLY this format with one blank line between questions:

Question: [question text]
A. [option one]
B. [option two]
C. [option three]
D. [option four]
Answer: [single correct letter: A, B, C, or D]
Explanation: [brief explanation of why this answer is correct]

# TOPIC
Write a single topic label (2-5 words) classifying this lecture (e.g. Machine Learning Fundamentals).

# KEYWORDS
Write exactly 15 important keywords and key phrases, comma-separated on a single line.

---
TRANSCRIPT:
{transcript}"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all_content(transcript: str) -> dict:
    """Single Gemini call that returns all academic content for a lecture."""
    prompt = _PROMPT_TEMPLATE.format(transcript=transcript)
    raw = _generate_with_retry(prompt)
    return _parse_response(raw)


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

def _get_client() -> genai.Client:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        raise RuntimeError(
            "GEMINI_API_KEY not found in Streamlit secrets. "
            "Add it to .streamlit/secrets.toml locally or in Streamlit Cloud App Settings."
        )
    return genai.Client(api_key=api_key)


def _generate_with_retry(prompt: str) -> str:
    client = _get_client()
    last_exc = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.65,
                ),
            )
            return response.text

        except Exception as exc:
            last_exc = exc
            if attempt == MAX_RETRIES:
                break
            wait = 2 ** attempt  # 1 → 2 → 4 → 8 → 16 seconds
            time.sleep(wait)

    raise RuntimeError(
        f"Gemini API failed after {MAX_RETRIES + 1} attempts. "
        f"Last error: {last_exc}"
    ) from last_exc


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(
    r'^#\s*(NOTES|FLASHCARDS|QUIZ|TOPIC|KEYWORDS)\s*$',
    re.MULTILINE | re.IGNORECASE,
)


def _parse_response(text: str) -> dict:
    result = {
        "notes": "",
        "flashcards": [],
        "quiz": [],
        "topic": "",
        "keywords": [],
    }

    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        # Fallback: treat entire response as notes
        result["notes"] = text.strip()
        return result

    for i, match in enumerate(matches):
        name = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        if name == "NOTES":
            result["notes"] = content
        elif name == "FLASHCARDS":
            result["flashcards"] = _parse_flashcards(content)
        elif name == "QUIZ":
            result["quiz"] = _parse_quiz(content)
        elif name == "TOPIC":
            result["topic"] = content.strip().strip("\"'").strip()
        elif name == "KEYWORDS":
            result["keywords"] = [
                k.strip() for k in re.split(r"[,\n]", content) if k.strip()
            ]

    return result


def _parse_flashcards(text: str) -> list:
    cards = []
    question = None
    answer_parts = []

    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r'^[Qq]:', stripped):
            if question is not None and answer_parts:
                cards.append({"question": question, "answer": " ".join(answer_parts).strip()})
            question = stripped[2:].strip()
            answer_parts = []
        elif re.match(r'^[Aa]:', stripped) and question is not None:
            answer_parts = [stripped[2:].strip()]
        elif question is not None and answer_parts and stripped:
            answer_parts.append(stripped)

    if question is not None and answer_parts:
        cards.append({"question": question, "answer": " ".join(answer_parts).strip()})

    return cards


def _parse_quiz(text: str) -> list:
    questions = []
    blocks = re.split(r'\n\s*\n', text.strip())

    for block in blocks:
        if not block.strip():
            continue

        q = {"question": "", "options": [], "correct": "", "explanation": ""}
        explanation_lines = []
        in_explanation = False

        for line in block.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            lower = stripped.lower()

            if lower.startswith("question:"):
                q["question"] = stripped[9:].strip()
                in_explanation = False
            elif re.match(r'^[A-Da-d][.\)]\s', stripped):
                letter = stripped[0].upper()
                q["options"].append(f"{letter}. {stripped[2:].strip()}")
                in_explanation = False
            elif lower.startswith("answer:"):
                ans = stripped[7:].strip().upper()
                q["correct"] = ans[0] if ans else ""
                in_explanation = False
            elif lower.startswith("explanation:"):
                explanation_lines = [stripped[12:].strip()]
                in_explanation = True
            elif in_explanation and stripped:
                explanation_lines.append(stripped)

        q["explanation"] = " ".join(explanation_lines).strip()

        if q["question"] and q["options"]:
            questions.append(q)

    return questions
