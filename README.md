# Classroom Co-Pilot AI

**Voice-Enabled AI Teaching Assistant for Haryana Government School Smart Classrooms**

A voice-first AI co-pilot that lets teachers explain concepts and run quizzes using natural Hinglish speech. Built on a **unified Mistral AI stack** — one API, three models, zero cross-vendor latency.

## Features

| Feature | Description |
|---------|-------------|
| **Voice In / Voice Out** | Teacher speaks Hinglish, AI responds with full spoken explanation + visuals |
| **Live Transcript** | Real-time word-by-word display as teacher speaks |
| **Interactive Diagrams** | SVG diagrams projected on smart board (photosynthesis, circuits, water cycle, etc.) |
| **Voice Quizzes** | *"Let's do a quiz!"* → AI generates 3-4 MCQ questions with instant grading |
| **NCERT RAG** | Curriculum-aligned responses using keyword retrieval over NCERT/Haryana Board data |
| **On-Screen Keyboard** | Virtual keyboard with EN/HI toggle for touch-screen smart boards |
| **Zero Config** | One API key, one command, done |

## How It Works

```
Teacher speaks into mic
        ↓
[voxtral-mini-latest]    →  STT: Hinglish speech → text
        ↓
[mistral-large-2512]     →  LLM: Structured JSON (Zod schema enforced)
        ↓
[voxtral-mini-tts-2603]  →  TTS: Full explanation → spoken audio
        ↓
Smart board displays: transcript + concept points + interactive diagram
```

**Three Mistral calls. One API key. ~3 second total latency.**

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | **Streamlit** | Rapid prototyping, smart board optimized |
| AI | **Mistral AI SDK** | Unified STT + LLM + TTS in one vendor |
| Schemas | **Pydantic** | Type-safe structured LLM output |
| RAG | **Keyword Retrieval** | NCERT curriculum-aligned responses |
| State | **Streamlit Session State** | Conversation history, settings persistence |

## Prompt Design

The LLM outputs **strict JSON** enforced by Pydantic schema:

```json
{
  "mode": "SIMPLIFY",
  "audio_speech": "6-10 sentences of full Hinglish explanation...",
  "screen_data": {
    "title": "Photosynthesis",
    "points": ["Sunlight energy...", "CO₂ absorption...", "Glucose production..."],
    "visual_cue": "Diagram showing sun, leaf, CO₂, O₂, water cycle"
  },
  "quiz_data": null
}
```

Key design choices:
- **Hinglish-first** — all prompts optimized for Hindi-English mix speech
- **Full audio_speech** — complete lesson (6-10 sentences), not just a summary
- **Schema-enforced** via `chat.parse` — SDK rejects malformed responses
- **Temperature 0.3** — deterministic, consistent classroom output
- **RAG context** — NCERT curriculum data injected as reference material

## Localization

| Language | Support |
|----------|---------|
| Hinglish (Hindi + English) | Primary — all speech I/O, prompts, responses |
| English | UI labels, error messages |
| Hindi (Devanagari) | On-screen keyboard input |

The system prompt is specifically designed for **Hinglish conversational flow** — using natural mixing of Hindi words ("bacho", "dekhte hain", "samjhe?") with English technical terms.

## Getting Started

### Prerequisites

- Python 3.10+
- A [Mistral AI](https://console.mistral.ai/) API key

### Install & Run

```bash
# Clone
git clone https://github.com/namandhakad712/school-copilot-streamlit
cd school-copilot-streamlit

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env.local
# Add your key: MISTRAL_API_KEY=your_key_here

# Run
streamlit run app.py
# → http://localhost:8501
```

## Project Structure

```
school-copilot-streamlit/
├── app.py                  # Main Streamlit application
├── lib/
│   ├── __init__.py
│   ├── client.py           # Mistral AI client (STT + LLM + TTS)
│   ├── curriculum.py       # NCERT curriculum data (RAG)
│   ├── rag.py              # Keyword-based RAG retrieval
│   └── schemas.py          # Pydantic models for structured output
├── requirements.txt
├── .env.example
└── README.md
```

## Deliverables

- **Live URL**: [Streamlit app running on localhost:8501]
- **GitHub Repo**: [https://github.com/namandhakad712/school-copilot-streamlit](https://github.com/namandhakad712/school-copilot-streamlit)
- **Video Walkthrough**: [3-minute demo video]
- **This README**: Tech stack, prompt design, localization details

## License

MIT
