# **EduScribe AI – Lecture Voice-to-Notes Generator**

# 1. Overview

EduScribe AI is an AI-powered educational platform that automatically converts lecture audio recordings into structured study materials. It is designed to help students focus on understanding lectures instead of worrying about taking notes.

Students often miss important information while simultaneously listening and writing notes. Revisiting recordings is time-consuming, and manually creating revision material such as notes, flashcards, and quizzes requires additional effort.

EduScribe AI solves this problem by processing lecture recordings using Artificial Intelligence to generate organized learning resources in minutes.

---

# 2. Key Features

### a) Lecture Audio Upload

Supports lecture recordings in:

* MP3
* WAV
* M4A

Users simply upload an audio recording to begin processing.

### b) AI Speech-to-Text

Uses **OpenAI Whisper (Base Model)** to accurately convert spoken lectures into text.

Generated transcript preserves the lecture content and serves as the foundation for all AI-generated study materials.

### c) AI Study Notes

Gemini AI converts the transcript into structured notes containing:

* Topic Overview
* Key Concepts
* Important Points
* Exam-Oriented Notes

This enables students to revise lectures quickly without reading the entire transcript.

### d) Interactive Flashcards

AI automatically generates flashcards from the lecture.

Each flashcard includes:

* Question
* Answer

Students can:

* Read the answer
* Flip the card
* Enter their own answer
* Receive AI-based evaluation
* Move to the next flashcard

This supports active recall learning.

### e) Interactive Quiz

EduScribe AI automatically generates multiple-choice questions from the lecture.

Students can:

* Select answers
* Submit responses
* View score
* Review correct answers
* Learn from explanations

The quiz encourages self-assessment after completing revision.

### f) Lecture Library

Every processed lecture is stored locally using SQLite.

Students can revisit previously generated:

* Transcript
* Notes
* Flashcards
* Quiz

without uploading the lecture again.

### g) PDF Export

Users can download a PDF containing:

* Lecture Transcript
* AI Generated Study Notes

This allows offline revision and sharing.

---

# 3. AI Processing Pipeline

The application follows the pipeline below:

```
Upload Lecture
        │
        ▼
Speech-to-Text (Whisper)
        │
        ▼
Generate Study Materials (Gemini)
        │
        ├── Transcript
        ├── Notes
        ├── Flashcards
        └── Quiz
        │
        ▼
Store in SQLite Database
        │
        ▼
View from Lecture Library
```

---

# 4. Technology Stack

## a) Frontend

* Streamlit

## b) Backend

* Python

## c) Database

* SQLite

## d) AI Models

### Speech Recognition

OpenAI Whisper (Base)

Used for:

* Speech-to-Text transcription

### e) Generative AI

Google Gemini 2.5 Flash

Used for:

* Study Notes
* Flashcards
* Quiz Generation
* Flashcard Evaluation

## f) Libraries

* Streamlit
* OpenAI Whisper
* Google GenAI
* PyTorch
* Pandas
* NumPy
* Pillow
* python-dotenv

---

# 5. Project Structure

```
EduScribeAI/

│
├── app.py
├── requirements.txt
├── packages.txt
├── assets/
├── pages/
├── services/
├── database/
├── .streamlit/
└── README.md
```

---

# 6. How This Helps Students

EduScribe AI improves learning by:

* Reducing manual note-taking.
* Saving revision time.
* Automatically organizing lecture material.
* Encouraging active recall using flashcards.
* Helping students self-assess using quizzes.
* Providing downloadable notes for offline study.

The platform transforms a single lecture recording into multiple learning resources automatically.

---

# 7. Accessing the Deployed Application

The EduScribe AI application is already deployed on Streamlit Community Cloud.

You can directly access and use the application without any local setup.

Application Link:

```
https://eduscribeai.streamlit.app/
```

Simply open the link in your browser and start using the platform.

---

# 8. Running the Project Locally (Optional)

If you prefer to run the application locally, follow the steps below.

## a) Clone the Repository

```bash
git clone https://github.com/sathw1ka06/AICTE-BATCH-1-MAY-Voice-to-Notes-Generator.git
cd EduScribeAI
```

## b) Create a Virtual Environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## c) Install Python Dependencies

```bash
pip install -r requirements.txt
```

## d) Install FFmpeg

FFmpeg is required for Whisper transcription.

Windows

Download and install FFmpeg from the official website and ensure it is added to the system PATH.

Linux

```bash
sudo apt install ffmpeg
```

macOS

```bash
brew install ffmpeg
```

## e) Configure Gemini API Key

Create the following file:

```
.streamlit/secrets.toml
```

Add:

```toml
GEMINI_API_KEY="YOUR_API_KEY"
```

Generate a free API key from Google AI Studio.

## f) Run the Application

```bash
streamlit run app.py
```

The application will open automatically in your default browser.

If not, visit:

```
http://localhost:8501
```

---

# 9. How Evaluators Can Use the Application

### Step 1

Open the deployed Streamlit application.

### Step 2

Navigate to **Upload Lecture**.

### Step 3

Upload a lecture recording in MP3, WAV, or M4A format.

### Step 4

Wait while the AI processing pipeline completes.

The application automatically:

* Transcribes the lecture.
* Generates study notes.
* Creates flashcards.
* Creates a quiz.
* Saves everything to the Lecture Library.

### Step 5

Open the generated lecture from the **Lecture Library**.

Review:

* Transcript
* Study Notes
* Flashcards
* Quiz

### Step 6

Download the Transcript + Notes PDF if required.

---

# 12. License

This project is developed for educational purposes as part of the **IBM SkillsBuild AI Internship** and demonstrates the application of Speech Recognition and Generative AI to improve learning and revision.
