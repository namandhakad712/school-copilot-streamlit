
```
░██    ░██                       ░██                                  ░██████                        ░██░██               ░██    
░██    ░██                       ░██                                 ░██   ░██                          ░██               ░██    
░██    ░██  ░██████    ░██████   ░██    ░██░██    ░██  ░██████      ░██         ░███████  ░████████  ░██░██  ░███████  ░████████ 
░██    ░██       ░██        ░██  ░██   ░██ ░██    ░██       ░██     ░██        ░██    ░██ ░██    ░██ ░██░██ ░██    ░██    ░██    
 ░██  ░██   ░███████   ░███████  ░███████  ░██    ░██  ░███████     ░██        ░██    ░██ ░██    ░██ ░██░██ ░██    ░██    ░██    
  ░██░██   ░██   ░██  ░██   ░██  ░██   ░██ ░██   ░███ ░██   ░██      ░██   ░██ ░██    ░██ ░███   ░██ ░██░██ ░██    ░██    ░██    
   ░███     ░█████░██  ░█████░██ ░██    ░██ ░█████░██  ░█████░██      ░██████   ░███████  ░██░█████  ░██░██  ░███████      ░████ 
                                                  ░██                                     ░██                                    
                                            ░███████                                      ░██                                    
                                                                                                                                    
```

### Voice-First AI Teaching Assistant for Haryana Government School Smart Classrooms

A hands-free, voice-first AI co-pilot that lets teachers explain concepts, run quizzes, translate content, and guide activities using natural Hinglish speech — all projected on the smart board.

**One API key. Three Mistral AI models. Zero cross-vendor latency.**

---

## Features

| Feature | What it does | Example command |
|---------|-------------|-----------------|
| **Live Concept Simplification** | Teacher speaks a topic → AI explains in Hinglish with visual points on smart board | *"Photosynthesis samjhao"* |
| **Voice-Triggered Quizzing** | AI generates 3 MCQ questions, displays on board, teacher quizzes verbally | *"Quiz lagao Newton's laws pe"* |
| **Bilingual Dictation & Translation** | Transcribe/translate between English, Hindi, and Hinglish | *"Iska Hindi mein translate karo"* |
| **Hands-Free Activity Guide** | Verbal step-by-step instructions with on-screen countdown timer | *"Activity guide do photosynthesis ki"* |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE INPUT (Mic / Text)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  🎙 STT: voxtral-mini-latest                                   │
│  Transcribes Hinglish speech → text                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  🧠 LLM: mistral-large-2512                                    │
│  Structured JSON output with Zod schema                        │
│  → mode | audio_speech | screen_data | quiz_data | translation │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  🔊 TTS: voxtral-mini-tts-2603                                 │
│  Full Hinglish explanation audio (12-18 sentences)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  📺 SMART BOARD OUTPUT                                         │
│  Transcript + Concept Points / Quiz / Translation / Timer       │
└─────────────────────────────────────────────────────────────────┘

Pipeline latency: ~3 seconds end-to-end
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Interface** | Streamlit | Rapid prototyping, smart board optimized, wide layout |
| **AI SDK** | Mistral AI (Python) | Unified STT + LLM + TTS in one vendor, one API key |
| **Structured Output** | `chat.parse` + Pydantic | Schema-enforced JSON — SDK rejects malformed responses |
| **RAG** | Keyword retrieval over NCERT curriculum | 30+ curriculum chunks covering Science & Math, Class 6-10 |
| **State** | Streamlit Session State | Conversation history, quiz scores, settings persistence |
| **Deployment** | Streamlit Cloud | One-click deploy, public URL for live demo |

---

## Prompt Design

The system prompt is the core of this project. Key design choices:

### Language
- **Hinglish-first**: All prompts optimized for Hindi-English mix speech
- Natural conversational fillers: *"achha"*, *"dekho"*, *"samjhe?"*, *"chalo"*
- Technical terms in English, explanations in Hindi transliteration
- Example: *"Bacho, aaj hum photosynthesis dekhenge! Sunlight se paudhe apna khana banate hain..."*

### Persona
- Passionate, energetic Hindi-medium teacher
- Calls students *"bacho"* and *"beta/beti"*
- Uses Indian real-life examples: cricket, Bollywood, street food, festivals
- Makes complex topics feel simple and fun

### Structured Output
- JSON schema enforced via `chat.parse` — no manual parsing
- `audio_speech`: 6-10 sentences of FULL explanation (not a summary)
- `screen_data`: title, bullet points, visual cue for smart board
- `quiz_data`: 3 questions with 4 options each
- `translation`: original + translated text
- `activity`: step-by-step instructions with duration

### Modes
| Mode | Trigger | Output |
|------|---------|--------|
| SIMPLIFY | *"samjhao"*, *"explain"*, *"batao"* | Full explanation + visual points |
| QUIZ | *"quiz"*, *"sawal"*, *"test"* | 3 MCQ questions |
| TRANSLATE | *"translate"*, *"Hindi mein"*, *"English mein"* | Bilingual text |
| ACTIVITY | *"activity"*, *"practical"*, *"experiment"* | Step-by-step guide + timer |

---

## Localization

| Language | Support |
|----------|---------|
| **Hinglish** (primary) | All speech I/O, prompts, responses in Hindi-English mix |
| **English** | UI labels, error messages, technical terms |
| **Hindi (Latin script)** | Transliterated Hindi in all interactions |
| **Hindi (Devanagari)** | On-screen keyboard input for non-Latin typing |

The system prompt specifically instructs the LLM to respond in **conversational Hinglish** — not pure Hindi, not pure English — matching how Haryana government school teachers actually speak.

---

## NCERT Curriculum RAG

The app includes a keyword-based RAG system with 30+ curriculum chunks:

**Science** (Class 6-10): Food, nutrition, light, electricity, force, sound, matter, atoms, cells, tissues, Newton's laws, gravitation, chemical reactions, acids/bases, metals, carbon compounds, life processes, control & coordination

**Mathematics** (Class 6-10): Numbers, fractions, geometry, integers, equations, perimeter/area, rational numbers, polynomials, triangles, trigonometry, quadratic equations, circles, statistics, probability

Each chunk includes: subject, class range, chapter, topic, keywords, and detailed content reference. The RAG retrieves the top 3 most relevant chunks and injects them as context for the LLM.

---

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
# Edit .env.local → MISTRAL_API_KEY=your_key

# Run
python -m streamlit run app.py
# → http://localhost:8501
```

### Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set `MISTRAL_API_KEY` in secrets
5. Deploy — get public URL

---

## Project Structure

```
school-copilot-streamlit/
├── app.py                  # Streamlit UI (dark glass-morphism, smart board optimized)
├── lib/
│   ├── __init__.py
│   ├── client.py           # Mistral AI pipeline (STT + LLM + TTS)
│   ├── curriculum.py       # NCERT curriculum data (30+ chunks)
│   ├── rag.py              # Keyword-based RAG retrieval
│   ├── schemas.py          # Pydantic models for structured output
│   └── visuals.py          # Universal visualization renderer
├── requirements.txt
├── .env.example
├── run.bat                 # Windows launcher
└── README.md
```

---

## Deliverables

- **Live URL**: Deployed on Streamlit Cloud
- **GitHub Repo**: [github.com/namandhakad712/school-copilot-streamlit](https://github.com/namandhakad712/school-copilot-streamlit)
- **README**: This document (tech stack, prompt design, localization)
- **Video Walkthrough**: 3-minute demo showing all 4 features

---

## License

MIT
