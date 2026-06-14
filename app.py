import base64
import json
import os
import time

import streamlit as st
from dotenv import load_dotenv

from lib.client import get_client, transcribe, generate_response, synthesize_speech, get_word_timestamps
from lib.visuals import render_interactive_visual

load_dotenv()

st.set_page_config(page_title="Classroom Co-Pilot AI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --primary: #00d4aa;
    --primary-dim: rgba(0,212,170,0.12);
    --purple: #7c3aed;
    --purple-dim: rgba(124,58,237,0.12);
    --blue: #3b82f6;
    --blue-dim: rgba(59,130,246,0.12);
    --amber: #f59e0b;
    --amber-dim: rgba(245,158,11,0.12);
    --red: #ef4444;
    --glass: rgba(255,255,255,0.03);
    --glass-border: rgba(255,255,255,0.06);
    --glass-hover: rgba(255,255,255,0.1);
    --text: rgba(255,255,255,0.92);
    --text2: rgba(255,255,255,0.55);
    --text3: rgba(255,255,255,0.3);
}

.stApp { background: #050510; font-family: 'Inter', sans-serif; }

/* ─── Hero ─── */
.hero {
    position: relative;
    background: linear-gradient(135deg, rgba(0,212,170,0.06) 0%, rgba(124,58,237,0.06) 100%);
    border: 1px solid rgba(0,212,170,0.1);
    border-radius: 20px;
    padding: 36px 44px;
    margin-bottom: 28px;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -15%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(0,212,170,0.05) 0%, transparent 70%);
    animation: glow 8s ease-in-out infinite alternate;
}
@keyframes glow {
    0% { transform: translate(0,0) scale(1); opacity: 0.5; }
    100% { transform: translate(30px,-20px) scale(1.15); opacity: 1; }
}
.hero h1 {
    font-size: 32px !important;
    font-weight: 900 !important;
    margin: 0 0 6px !important;
    background: linear-gradient(135deg, #00d4aa 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    position: relative;
    z-index: 1;
}
.hero-sub {
    color: var(--text2);
    font-size: 14px;
    margin: 0;
    position: relative;
    z-index: 1;
}

/* ─── Section Headers ─── */
.section-label {
    color: rgba(255,255,255,0.5);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    margin-bottom: 10px;
}

/* ─── Example Chips ─── */
.example-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}
.chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid var(--glass-border);
    background: var(--glass);
    color: var(--text2);
    cursor: pointer;
    transition: all 0.2s;
}
.chip:hover {
    border-color: var(--glass-hover);
    color: var(--text);
    transform: translateY(-1px);
}

/* ─── Glass Panel ─── */
.glass {
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
}

/* ─── Point Cards ─── */
.point-card {
    background: var(--glass);
    border-left: 3px solid var(--primary);
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 8px 0;
    color: var(--text2);
    font-size: 14px;
    line-height: 1.6;
}
.point-card strong { color: var(--primary); }

/* ─── Quiz ─── */
.quiz-badge {
    display: inline-block;
    background: var(--purple-dim);
    color: #a78bfa;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 6px;
    margin-right: 8px;
}
.quiz-q {
    color: var(--text);
    font-size: 15px;
    font-weight: 600;
    margin: 20px 0 10px;
}

/* ─── Translation ─── */
.trans-card {
    background: linear-gradient(135deg, rgba(124,58,237,0.05), rgba(59,130,246,0.05));
    border: 1px solid rgba(124,58,237,0.12);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
}

/* ─── Activity Timer ─── */
.timer-box {
    background: linear-gradient(135deg, rgba(245,158,11,0.05), rgba(245,158,11,0.02));
    border: 1px solid rgba(245,158,11,0.12);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
}
.timer-num {
    font-size: 52px;
    font-weight: 900;
    color: var(--amber);
    font-variant-numeric: tabular-nums;
    letter-spacing: 2px;
    margin: 12px 0;
}
.timer-step {
    color: var(--text2);
    font-size: 14px;
    padding: 10px 16px;
    margin: 6px 0;
    border-radius: 10px;
    background: var(--glass);
    text-align: left;
}
.timer-step.active {
    color: var(--amber);
    background: var(--amber-dim);
    font-weight: 600;
    border-left: 3px solid var(--amber);
}

/* ─── Visual Cue ─── */
.visual-cue {
    background: linear-gradient(135deg, rgba(0,212,170,0.04), transparent);
    border: 1px solid rgba(0,212,170,0.1);
    border-radius: 14px;
    padding: 20px;
    margin-top: 16px;
    text-align: center;
}
.visual-cue-label {
    color: var(--primary);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    margin-bottom: 8px;
}
.visual-cue-text {
    color: var(--text2);
    font-size: 13px;
    font-style: italic;
    line-height: 1.6;
}

/* ─── Timing ─── */
.timing-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.timing-chip {
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 11px;
    color: var(--text3);
}
.timing-chip b { color: var(--text2); }

/* ─── Transcript ─── */
.transcript-box {
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 20px;
}

/* ─── Score ─── */
.score-bar {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 14px 18px;
    margin-top: 12px;
}
.score-ring {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    border: 3px solid var(--glass-border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 800;
    color: var(--primary);
    flex-shrink: 0;
}

/* ─── Empty State ─── */
.empty-state {
    border: 1px dashed var(--glass-border);
    border-radius: 16px;
    padding: 80px 32px;
    text-align: center;
}
.empty-icon { font-size: 64px; margin-bottom: 20px; opacity: 0.35; }
.empty-title { color: var(--text2); font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.empty-sub { color: var(--text3); font-size: 13px; line-height: 1.7; }

/* ─── Sidebar — FORCE ALL TEXT WHITE ─── */
section[data-testid="stSidebar"] { background: #080818 !important; width: 340px !important; min-width: 340px !important; }
section[data-testid="stSidebar"] > div { padding: 0 16px !important; }
section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
section[data-testid="stSidebar"] label { color: white !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] { background: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.15) !important; }
section[data-testid="stSidebar"] [data-baseweb="input"] { background: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.15) !important; }
section[data-testid="stSidebar"] [data-baseweb="slider"] { accent-color: #00d4aa !important; }
section[data-testid="stSidebar"] button { background: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.1) !important; color: white !important; }
section[data-testid="stSidebar"] button:hover { background: rgba(0,212,170,0.15) !important; border-color: #00d4aa !important; }
section[data-testid="stSidebar"] [data-testid="stExpander"] { background: rgba(255,255,255,0.03) !important; border-color: rgba(255,255,255,0.08) !important; }

/* Fix: when sidebar collapsed, content should fill full width */
[data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    width: 0px !important;
    min-width: 0px !important;
    overflow: hidden !important;
}
.main .block-container {
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    transition: all 0.3s ease !important;
}

/* Streamlit overrides */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,212,170,0.2);
}
.stRadio > div { gap: 6px !important; }
.stRadio > div > label {
    background: var(--glass) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    transition: all 0.2s !important;
}
.stRadio > div > label:hover {
    border-color: var(--glass-hover) !important;
}
.stRadio > div > label[data-checked="true"] {
    border-color: var(--primary) !important;
    background: var(--primary-dim) !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def init_session():
    defaults = {
        "history": [], "status": "idle", "last_response": None, "last_audio": None,
        "last_transcript": "", "last_timing": {}, "last_words": [],
        "quiz_score": {"correct": 0, "total": 0},
        "processing": False, "last_ask_time": 0,
        "last_audio_hash": "",  # track processed audio to auto-submit new recordings
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════
# VOICE CATALOG — All 30 Mistral TTS preset voices
# ═══════════════════════════════════════════════════════════════
VOICE_CATALOG = {
    "English (US)": [
        ("en_paul_neutral", "Paul — Warm male, neutral tone"),
        ("en_oliver_confident", "Oliver — Confident male"),
        ("en_jane_neutral", "Jane — Friendly female"),
        ("en_marie_confident", "Marie — Confident female"),
        ("en_alexandra_confident", "Alexandra — Bold female"),
        ("en_andrew_confident", "Andrew — Deep male"),
        ("en_bella_confident", "Bella — Elegant female"),
        ("en_leo_confident", "Leo — Energetic male"),
    ],
    "English (UK)": [
        ("gb_jane_confident", "Jane — British female"),
        ("gb_geoffrey_confident", "Geoffrey — British male"),
        ("gb_charlotte_confident", "Charlotte — British elegant female"),
        ("gb_james_confident", "James — British male"),
    ],
    "French": [
        ("fr_alexandre_confident", "Alexandre — French male"),
        ("fr_delphine_confident", "Delphine — French female"),
        ("fr_henri_confident", "Henri — French male"),
    ],
    "German": [
        ("de_klaus_confident", "Klaus — German male"),
        ("de_lotte_confident", "Lotte — German female"),
    ],
    "Spanish": [
        ("es_elsa_confident", "Elsa — Spanish female"),
        ("es_alejandro_confident", "Alejandro — Spanish male"),
    ],
    "Italian": [
        ("it_giulia_confident", "Giulia — Italian female"),
        ("it_lorenzo_confident", "Lorenzo — Italian male"),
    ],
    "Portuguese": [
        ("pt_ricardo_confident", "Ricardo — Portuguese male"),
        ("pt_fernanda_confident", "Fernanda — Portuguese female"),
    ],
}

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — All settings live here, clean and organized
# ═══════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:12px 0 20px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:20px;">
            <div style="font-size:28px;margin-bottom:6px;">🎓</div>
            <div style="color:white;font-size:14px;font-weight:700;">Co-Pilot Settings</div>
        </div>
        """, unsafe_allow_html=True)

        # ─── API Key ───
        env_key = os.getenv("MISTRAL_API_KEY", "")
        if env_key:
            st.markdown("""
            <div style="background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.2);border-radius:8px;padding:8px 12px;margin-bottom:12px;">
                <span style="color:#00d4aa;font-size:11px;font-weight:700;">API Key</span><br>
                <span style="color:rgba(255,255,255,0.5);font-size:11px;">Loaded from environment</span>
            </div>
            """, unsafe_allow_html=True)
            api_key = env_key
        else:
            api_key = st.text_input(
                "🔑 API Key",
                value="",
                type="password",
                placeholder="sk-...",
            )

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        # ─── Voice Selection ───
        voice_options = []
        voice_labels = []
        for lang, voices in VOICE_CATALOG.items():
            for vid, vdesc in voices:
                voice_options.append(vid)
                voice_labels.append(f"{lang}: {vdesc}")

        default_idx = voice_options.index("en_paul_neutral") if "en_paul_neutral" in voice_options else 0
        voice_id = st.selectbox(
            "🔊 Output Voice",
            voice_options,
            index=default_idx,
            format_func=lambda v: next((l for o, l in zip(voice_options, voice_labels) if o == v), v),
        )

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
            border-radius:8px;padding:8px 12px;margin-top:4px;">
            <span style="color:rgba(255,255,255,0.3);font-size:10px;">VOICE ID</span><br>
            <code style="color:#00d4aa;font-size:11px;">{voice_id}</code>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        # ─── Class & Subject ───
        col1, col2 = st.columns(2)
        with col1:
            class_level = st.selectbox("📚 Class", ["", "6", "7", "8", "9", "10"],
                                       format_func=lambda x: f"Class {x}" if x else "Auto")
        with col2:
            subject = st.selectbox("📖 Subject", ["auto", "Science", "Math"],
                                   format_func=lambda x: "All" if x == "auto" else x)

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        # ─── Advanced Settings ───
        temperature = 0.4
        max_tokens = 4000
        with st.expander("⚙️ Advanced Settings", expanded=False):
            temperature = st.slider("Creativity", 0.0, 1.0, 0.4, 0.05)
            max_tokens = st.slider("Max Response Length", 2000, 6000, 4000, 500)

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

        # ─── Quick Examples ───
        examples = [
            ("Photosynthesis samjhao", "🔬 Concept"),
            ("Newton laws ka quiz banao", "🧩 Quiz"),
            ("Mitochondria translate karo", "🌐 Translate"),
            ("Science experiment batao", "🧪 Activity"),
            ("Periodic table samjhao", "🧬 Periodic Table"),
            ("Pythagoras theorem padhao", "📐 Theorem"),
        ]
        for query, label in examples:
            if st.button(label, key=f"ex_{query}", use_container_width=True):
                st.session_state["example_query"] = query
                st.rerun()

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

        # ─── Score ───
        if st.session_state.quiz_score["total"] > 0:
            sc = st.session_state.quiz_score
            pct = int(sc["correct"] / sc["total"] * 100)
            st.markdown(f"""
            <div class="score-bar">
                <div class="score-ring">{pct}%</div>
                <div>
                    <div style="color:rgba(255,255,255,0.8);font-weight:600;font-size:13px;">Quiz Score</div>
                    <div style="color:rgba(255,255,255,0.4);font-size:12px;">{sc['correct']}/{sc['total']} correct</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ─── History ───
        if st.session_state.history:
            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            st.markdown('<p style="color:white;font-size:13px;font-weight:700;margin-bottom:4px;">📋 Recent</p>', unsafe_allow_html=True)
            for entry in reversed(st.session_state.history[-5:]):
                icon = "🎙" if entry["role"] == "user" else "🤖"
                text = entry["content"][:50] + ("..." if len(entry["content"]) > 50 else "")
                st.markdown(f'<div style="color:rgba(255,255,255,0.4);font-size:11px;padding:3px 0;">{icon} {text}</div>', unsafe_allow_html=True)
            if st.button("Clear", use_container_width=True):
                st.session_state.history = []
                st.session_state.quiz_score = {"correct": 0, "total": 0}
                st.rerun()

    return api_key, class_level, subject, voice_id, temperature, max_tokens


# ═══════════════════════════════════════════════════════════════
# RENDER FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def render_simplify(response):
    if not response.screen_data:
        return
    sd = response.screen_data
    st.markdown(f'<div style="color:var(--primary);font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:6px;">Concept</div>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="color:var(--text);font-size:20px;font-weight:700;margin:0 0 16px;">{sd.title}</h3>', unsafe_allow_html=True)
    for i, p in enumerate(sd.points):
        st.markdown(f'<div class="point-card"><strong>{i+1}.</strong> {p}</div>', unsafe_allow_html=True)
    if sd.visual_cue:
        st.markdown(f"""
        <div class="visual-cue">
            <div class="visual-cue-label">Smart Board</div>
            <div class="visual-cue-text">{sd.visual_cue}</div>
        </div>
        """, unsafe_allow_html=True)


def render_quiz(response):
    if not response.quiz_data:
        return
    qd = response.quiz_data
    st.markdown(f'<div style="color:#a78bfa;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:6px;">Quiz</div>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="color:var(--text);font-size:20px;font-weight:700;margin:0 0 20px;">{qd.topic}</h3>', unsafe_allow_html=True)
    for qi, q in enumerate(qd.questions):
        st.markdown(f'<div class="quiz-q"><span class="quiz-badge">Q{qi+1}</span>{q.question}</div>', unsafe_allow_html=True)
        sel = st.radio("Answer", q.options, key=f"quiz_{qi}", label_visibility="collapsed")
        idx = q.options.index(sel) if sel in q.options else -1
        if idx == q.correct_index:
            st.markdown('<div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);border-radius:10px;padding:10px 14px;color:#34d399;font-weight:600;font-size:13px;">Correct!</div>', unsafe_allow_html=True)
            if not st.session_state.get(f"qc_{qi}"):
                st.session_state.quiz_score["correct"] += 1
                st.session_state.quiz_score["total"] += 1
                st.session_state[f"qc_{qi}"] = True
        elif idx != -1:
            st.markdown(f'<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:10px 14px;color:#ef4444;font-size:13px;">Wrong — Answer: <b>{q.options[q.correct_index]}</b></div>', unsafe_allow_html=True)
            if not st.session_state.get(f"qc_{qi}"):
                st.session_state.quiz_score["total"] += 1
                st.session_state[f"qc_{qi}"] = True


def render_translation(response):
    if not response.translation:
        return
    t = response.translation
    st.markdown(f"""
    <div class="trans-card">
        <div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Original</div>
        <div style="color:rgba(255,255,255,0.5);font-size:16px;margin-bottom:24px;">{t.get('original','')}</div>
        <div style="color:var(--text3);font-size:28px;margin-bottom:24px;">↓</div>
        <div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Translated</div>
        <div style="color:var(--text);font-size:24px;font-weight:700;">{t.get('translated','')}</div>
        <div style="color:var(--text3);font-size:11px;margin-top:14px;text-transform:uppercase;letter-spacing:1px;">{t.get('language','')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_activity(response):
    if not response.activity:
        return
    a = response.activity
    dur = a.get("duration_seconds", 300)
    steps = a.get("steps", [])
    st.markdown(f'<div style="color:var(--amber);font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:6px;">Activity</div>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="color:var(--text);font-size:18px;font-weight:700;margin:0 0 6px;">{a.get("instruction","")}</h3>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:var(--text3);font-size:12px;margin-bottom:20px;">{dur//60} min {dur%60} sec</div>', unsafe_allow_html=True)
    ph = st.empty()
    if st.button("Start Timer", type="primary", use_container_width=True):
        for rem in range(dur, 0, -1):
            m, s = divmod(rem, 60)
            act = len(steps) - 1 if steps else 0
            for si in range(len(steps)):
                if rem > dur - (dur / len(steps)) * (si + 1):
                    act = si; break
            sh = "".join(f'<div class="timer-step {"active" if i==act else ""}">{i+1}. {st2}</div>' for i, st2 in enumerate(steps))
            ph.markdown(f'<div class="timer-box"><div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1px;">Remaining</div><div class="timer-num">{m:02d}:{s:02d}</div>{sh}</div>', unsafe_allow_html=True)
            time.sleep(1)
        ph.markdown('<div class="timer-box"><div class="timer-num" style="color:#34d399;">DONE!</div><div style="color:#34d399;font-weight:600;">Complete</div></div>', unsafe_allow_html=True)
    else:
        m, s = divmod(dur, 60)
        sh = "".join(f'<div class="timer-step">{i+1}. {st2}</div>' for i, st2 in enumerate(steps))
        ph.markdown(f'<div class="timer-box"><div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1px;">Duration</div><div class="timer-num">{m:02d}:{s:02d}</div>{sh}</div>', unsafe_allow_html=True)


def render_timing(timing):
    chips = []
    for k, l in [("stt_ms","STT"),("llm_ms","LLM"),("tts_ms","TTS"),("total_ms","Total")]:
        if k in timing and timing[k]:
            chips.append(f'<span class="timing-chip">{l}: <b>{timing[k]}ms</b></span>')
    if chips:
        st.markdown(f'<div class="timing-bar">{"".join(chips)}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# KARAOKE CAPTIONS — Word-level synced captions
# ═══════════════════════════════════════════════════════════════
def render_karaoke_captions(audio_b64: str, words: list[dict], speech_text: str):
    """Render karaoke-style word-synced captions with audio playback."""
    if not audio_b64 or not words:
        # Fallback: simple transcript display
        if speech_text:
            st.markdown(f"""
            <div style="background:var(--glass);border:1px solid var(--glass-border);border-radius:14px;padding:20px;margin:12px 0;">
                <div style="color:var(--primary);font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;">Spoken Text</div>
                <div style="color:var(--text);font-size:15px;line-height:1.8;">{speech_text}</div>
            </div>
            """, unsafe_allow_html=True)
        return

    words_json = json.dumps(words)
    st.markdown(f"""
    <div id="karaoke-box" style="background:linear-gradient(135deg,rgba(0,212,170,0.04),rgba(124,58,237,0.04));
        border:1px solid rgba(0,212,170,0.12);border-radius:14px;padding:20px;margin:12px 0;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#ef4444;animation:pulse 1s infinite;"></div>
            <span style="color:var(--primary);font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;">Live Captions</span>
        </div>
        <div id="caption-text" style="color:var(--text);font-size:18px;line-height:2;min-height:60px;font-weight:500;">
            <span style="color:var(--text3);">Waiting for audio...</span>
        </div>
        <div style="display:flex;gap:8px;margin-top:12px;align-items:center;">
            <div id="caption-progress" style="flex:1;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;">
                <div id="caption-progress-fill" style="height:100%;width:0%;background:linear-gradient(90deg,#00d4aa,#7c3aed);border-radius:2px;transition:width 0.1s;"></div>
            </div>
            <span id="caption-time" style="color:var(--text3);font-size:11px;font-variant-numeric:tabular-nums;">0:00</span>
        </div>
    </div>

    <script>
    (function() {{
        const words = {words_json};
        const audioB64 = "{audio_b64}";
        const captionEl = document.getElementById('caption-text');
        const progressFill = document.getElementById('caption-progress-fill');
        const timeEl = document.getElementById('caption-time');

        // Create audio element
        const audio = new Audio('data:audio/mp3;base64,' + audioB64);
        audio.id = 'karaoke-audio';

        // Insert audio player before karaoke box
        const box = document.getElementById('karaoke-box');
        const playerDiv = document.createElement('div');
        playerDiv.style.cssText = 'margin-bottom:12px;';
        playerDiv.appendChild(audio);
        audio.style.cssText = 'width:100%;border-radius:8px;outline:none;height:40px;';
        box.insertBefore(playerDiv, box.children[1]);

        let currentIdx = -1;

        function updateCaption() {{
            if (!audio.paused && !audio.ended) {{
                const t = audio.currentTime;

                // Find current word
                let idx = -1;
                for (let i = 0; i < words.length; i++) {{
                    if (t >= words[i].start && t <= words[i].end) {{
                        idx = i;
                        break;
                    }}
                }}

                // Update display
                if (idx !== currentIdx) {{
                    currentIdx = idx;
                    let html = '';
                    for (let i = 0; i < words.length; i++) {{
                        const w = words[i];
                        const isPast = t > w.end;
                        const isCurrent = i === idx;
                        let style = 'padding:2px 3px;border-radius:4px;transition:all 0.15s;display:inline-block;margin:2px 0;';
                        if (isCurrent) {{
                            style += 'background:rgba(0,212,170,0.2);color:#00d4aa;font-weight:700;transform:scale(1.05);';
                        }} else if (isPast) {{
                            style += 'color:rgba(255,255,255,0.35);';
                        }} else {{
                            style += 'color:rgba(255,255,255,0.7);';
                        }}
                        html += '<span style="' + style + '">' + w.word + '</span> ';
                    }}
                    captionEl.innerHTML = html;
                }}

                // Progress
                if (audio.duration) {{
                    progressFill.style.width = (t / audio.duration * 100) + '%';
                    const m = Math.floor(t / 60);
                    const s = Math.floor(t % 60);
                    timeEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
                }}

                requestAnimationFrame(updateCaption);
            }}
        }}

        audio.addEventListener('play', () => requestAnimationFrame(updateCaption));
        audio.addEventListener('ended', () => {{
            captionEl.innerHTML = '<span style="color:var(--text3);">Playback complete</span>';
            progressFill.style.width = '100%';
        }});
    }})();
    </script>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# EXPORT — Generate stylish standalone HTML
# ═══════════════════════════════════════════════════════════════
def generate_export_html(response, transcript: str, audio_b64: str = "", words: list[dict] | None = None) -> str:
    """Generate a self-contained stylish HTML file with ALL sections."""

    # ─── Mode-specific content ───
    mode_section = ""

    if response.mode == "SIMPLIFY" and response.screen_data:
        sd = response.screen_data
        points_html = "".join(
            f'<div style="background:rgba(0,212,170,0.04);border-left:3px solid #00d4aa;border-radius:0 10px 10px 0;padding:14px 18px;margin:8px 0;color:rgba(255,255,255,0.7);font-size:15px;line-height:1.6;"><strong style="color:#00d4aa;">{i+1}.</strong> {p}</div>'
            for i, p in enumerate(sd.points)
        )
        cue_html = ""
        if sd.visual_cue:
            cue_html = f"""
            <div style="background:linear-gradient(135deg,rgba(0,212,170,0.04),transparent);border:1px solid rgba(0,212,170,0.1);border-radius:14px;padding:20px;margin-top:16px;text-align:center;">
                <div style="color:#00d4aa;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;">Smart Board</div>
                <div style="color:rgba(255,255,255,0.5);font-size:13px;font-style:italic;">{sd.visual_cue}</div>
            </div>"""
        mode_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#00d4aa;">Concept</div>
            <h2 style="color:white;font-size:24px;font-weight:800;margin:0 0 16px;background:linear-gradient(135deg,#00d4aa,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{sd.title}</h2>
            {points_html}
            {cue_html}
        </div>"""

    elif response.mode == "QUIZ" and response.quiz_data:
        qd = response.quiz_data
        qs_html = ""
        for qi, q in enumerate(qd.questions):
            opts = "".join(
                f'<div style="padding:8px 14px;margin:4px 0;border-radius:8px;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.5);font-size:14px;">{chr(65+j)}. {o}</div>'
                for j, o in enumerate(q.options)
            )
            qs_html += f'<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:16px;margin:12px 0;"><div style="color:rgba(255,255,255,0.85);font-weight:600;margin-bottom:8px;">Q{qi+1}. {q.question}</div>{opts}<div style="color:#34d399;font-size:12px;margin-top:6px;">Answer: {q.options[q.correct_index]}</div></div>'
        mode_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#a78bfa;">Quiz</div>
            <h2 style="color:white;font-size:22px;font-weight:800;margin:0 0 16px;">{qd.topic}</h2>
            {qs_html}
        </div>"""

    elif response.mode == "TRANSLATE" and response.translation:
        t = response.translation
        mode_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#60A5FA;">Translation</div>
            <div style="background:linear-gradient(135deg,rgba(124,58,237,0.05),rgba(59,130,246,0.05));border:1px solid rgba(124,58,237,0.12);border-radius:16px;padding:32px;text-align:center;">
                <div style="color:rgba(255,255,255,0.4);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Original</div>
                <div style="color:rgba(255,255,255,0.6);font-size:16px;margin-bottom:24px;">{t.get("original","")}</div>
                <div style="color:rgba(255,255,255,0.2);font-size:28px;margin-bottom:24px;">↕</div>
                <div style="color:rgba(255,255,255,0.4);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Translated</div>
                <div style="color:white;font-size:22px;font-weight:700;">{t.get("translated","")}</div>
                <div style="color:rgba(255,255,255,0.3);font-size:11px;margin-top:14px;">{t.get("language","")}</div>
            </div>
        </div>"""

    elif response.mode == "ACTIVITY" and response.activity:
        a = response.activity
        dur = a.get("duration_seconds", 0)
        steps_html = "".join(
            f'<div style="padding:10px 16px;margin:5px 0;background:rgba(255,255,255,0.04);border-radius:10px;color:rgba(255,255,255,0.6);font-size:14px;border-left:3px solid #f59e0b;"><b style="color:#f59e0b;">{i+1}.</b> {s}</div>'
            for i, s in enumerate(a.get("steps", []))
        )
        mode_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#f59e0b;">Activity</div>
            <h2 style="color:white;font-size:20px;font-weight:800;margin:0 0 8px;">{a.get("instruction","")}</h2>
            <div style="color:rgba(255,255,255,0.3);font-size:12px;margin-bottom:16px;">Duration: {dur//60} min {dur%60} sec</div>
            {steps_html}
        </div>"""

    # ─── Spoken Text (TTS content) ───
    spoken_section = ""
    if response.audio_speech:
        spoken_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#f59e0b;">Spoken Text (TTS)</div>
            <div style="background:rgba(245,158,11,0.04);border:1px solid rgba(245,158,11,0.1);border-radius:12px;padding:20px;">
                <div style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.8;white-space:pre-wrap;">{response.audio_speech}</div>
            </div>
        </div>"""

    # ─── Subtitles ───
    subtitles_section = ""
    if words:
        sub_lines = []
        for w in words:
            m_s = int(w["start"] // 60)
            s_s = int(w["start"] % 60)
            m_e = int(w["end"] // 60)
            s_e = int(w["end"] % 60)
            sub_lines.append(f'<div class="sub-line"><span class="sub-time">{m_s:02d}:{s_s:02d} → {m_e:02d}:{s_e:02d}</span> <span class="sub-word">{w["word"]}</span></div>')
        subtitles_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#7c3aed;">Subtitles</div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px;max-height:300px;overflow-y:auto;font-family:monospace;font-size:13px;">
                {"".join(sub_lines)}
            </div>
        </div>"""

    # ─── Audio ───
    audio_section = ""
    if audio_b64:
        audio_section = f"""
        <div class="section-block">
            <div class="section-tag" style="color:#ef4444;">Audio</div>
            <audio controls style="width:100%;border-radius:8px;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Classroom Co-Pilot — {response.mode}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',system-ui,sans-serif;background:#050510;color:rgba(255,255,255,0.85);min-height:100vh;padding:32px;}}
.container{{max-width:900px;margin:0 auto;}}
.header{{text-align:center;margin-bottom:40px;padding:32px;background:linear-gradient(135deg,rgba(0,212,170,0.06),rgba(124,58,237,0.06));border:1px solid rgba(0,212,170,0.1);border-radius:20px;}}
.header h1{{font-size:28px;font-weight:900;background:linear-gradient(135deg,#00d4aa,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;}}
.header .meta{{color:rgba(255,255,255,0.3);font-size:12px;}}
.transcript-bar{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px 20px;margin-bottom:32px;}}
.transcript-bar .label{{color:rgba(255,255,255,0.3);font-size:10px;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;}}
.transcript-bar .text{{color:rgba(255,255,255,0.85);font-size:15px;}}
.section-block{{margin-bottom:32px;}}
.section-tag{{font-size:11px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:12px;}}
.sub-line{{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);}}
.sub-time{{color:rgba(255,255,255,0.25);font-size:11px;margin-right:8px;}}
.sub-word{{color:rgba(255,255,255,0.7);}}
.sub-line:hover .sub-word{{color:#00d4aa;}}
.sub-line:hover{{background:rgba(0,212,170,0.03);}}
.footer{{text-align:center;margin-top:40px;padding:20px;border-top:1px solid rgba(255,255,255,0.06);color:rgba(255,255,255,0.2);font-size:11px;}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Classroom Co-Pilot AI</h1>
        <div class="meta">Generated by Classroom Co-Pilot AI — Voice-First Teaching Assistant</div>
    </div>

    <div class="transcript-bar">
        <div class="label">Teacher's Question</div>
        <div class="text">{transcript}</div>
    </div>

    {audio_section}
    {mode_section}
    {spoken_section}
    {subtitles_section}

    <div class="footer">
        Classroom Co-Pilot AI — Built for Haryana Government School Smart Classrooms
    </div>
</div>
</body>
</html>"""


def render_smart_board(response):
    if response.mode == "SIMPLIFY":
        vis = getattr(response, "visualization", None)
        sd = response.screen_data
        title = sd.title if sd else ""
        points = sd.points if sd else []
        cue = sd.visual_cue if sd else ""
        render_interactive_visual(vis, title=title, points=points, visual_cue=cue)

    elif response.mode == "QUIZ" and response.quiz_data:
        qd = response.quiz_data
        qs = ""
        for qi, q in enumerate(qd.questions):
            opts = "".join(f'<div style="padding:6px 12px;margin:3px 0;border-radius:8px;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.5);font-size:13px;">{chr(65+j)}. {o}</div>' for j, o in enumerate(q.options))
            qs += f'<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:16px;margin:10px 0;"><div style="color:rgba(255,255,255,0.85);font-weight:600;margin-bottom:8px;">Q{qi+1}. {q.question}</div>{opts}</div>'
        st.markdown(f'<div style="background:linear-gradient(135deg,rgba(124,58,237,0.05),rgba(124,58,237,0.01));border:1px solid rgba(124,58,237,0.1);border-radius:16px;padding:28px;min-height:300px;"><div style="text-align:center;margin-bottom:16px;"><div style="color:#a78bfa;font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;">Quiz Board</div><h2 style="color:white;margin:0;font-size:20px;font-weight:700;">{qd.topic}</h2></div>{qs}</div>', unsafe_allow_html=True)

    elif response.mode == "TRANSLATE" and response.translation:
        t = response.translation
        st.markdown(f'<div style="background:linear-gradient(135deg,rgba(124,58,237,0.05),rgba(59,130,246,0.05));border:1px solid rgba(124,58,237,0.1);border-radius:16px;padding:32px;min-height:300px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;"><div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Original</div><div style="color:rgba(255,255,255,0.5);font-size:16px;margin-bottom:20px;max-width:80%;">{t.get("original","")}</div><div style="color:var(--text3);font-size:28px;margin-bottom:20px;">↕</div><div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Translated</div><div style="color:white;font-size:22px;font-weight:700;max-width:80%;">{t.get("translated","")}</div><div style="color:var(--text3);font-size:11px;margin-top:14px;">{t.get("language","")}</div></div>', unsafe_allow_html=True)

    elif response.mode == "ACTIVITY" and response.activity:
        a = response.activity
        dur = a.get("duration_seconds", 0)
        ss = "".join(f'<div style="padding:10px 16px;margin:5px 0;background:rgba(255,255,255,0.04);border-radius:10px;color:rgba(255,255,255,0.6);font-size:14px;border-left:3px solid var(--amber);"><b style="color:var(--amber);">{i+1}.</b> {s}</div>' for i, s in enumerate(a.get("steps", [])))
        st.markdown(f'<div style="background:linear-gradient(135deg,rgba(245,158,11,0.05),rgba(245,158,11,0.01));border:1px solid rgba(245,158,11,0.1);border-radius:16px;padding:28px;min-height:300px;"><div style="text-align:center;margin-bottom:16px;"><div style="color:var(--amber);font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;">Activity Board</div><h2 style="color:white;margin:0;font-size:18px;font-weight:700;">{a.get("instruction","")}</h2><div style="color:var(--text3);font-size:12px;margin-top:6px;">{dur//60} min {dur%60} sec</div></div>{ss}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    init_session()
    api_key, class_level, subject, voice_id, temperature, max_tokens = render_sidebar()

    # Hero
    st.markdown("""
    <div class="hero">
        <h1>Classroom Co-Pilot AI</h1>
        <p class="hero-sub">Voice-first AI assistant for Haryana government school teachers</p>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.markdown("""
        <div class="glass" style="text-align:center;padding:48px 32px;">
            <div style="font-size:48px;margin-bottom:16px;">🔑</div>
            <div style="color:var(--text);font-size:16px;font-weight:600;margin-bottom:6px;">API Key Required</div>
            <div style="color:var(--text3);font-size:13px;">Enter your Mistral API key in the sidebar to begin.<br>Get one free at <a href="https://console.mistral.ai" target="_blank" style="color:var(--primary);">console.mistral.ai</a></div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    client = get_client(api_key)

    # Input
    audio_value = st.audio_input("Record your question")

    example_q = st.session_state.pop("example_query", "")
    text_value = st.text_input("question", value=example_q, placeholder="Type or speak in Hinglish...", label_visibility="collapsed")

    # Auto-detect new voice recording and submit
    auto_submit = False
    if audio_value and not st.session_state.processing:
        ab = audio_value.getvalue()
        if ab:
            import hashlib
            audio_hash = hashlib.md5(ab).hexdigest()
            if audio_hash != st.session_state.last_audio_hash:
                auto_submit = True
                st.session_state.last_audio_hash = audio_hash

    c1, c2 = st.columns([1, 4])
    with c1:
        is_processing = st.session_state.processing
        ask = st.button("Ask", type="primary", use_container_width=True, disabled=is_processing,
                        help="Processing..." if is_processing else "Ask a question")

    if (ask or auto_submit) and not is_processing:
        # Debounce: reject if less than 2 seconds since last ask
        now = time.time()
        if now - st.session_state.last_ask_time < 2:
            st.info("Please wait..."); st.stop()
        st.session_state.last_ask_time = now
        st.session_state.processing = True

        transcript = ""
        stt_ms = 0
        if audio_value:
            ab = audio_value.getvalue()
            if ab:
                with st.spinner("Transcribing..."):
                    t0 = time.time()
                    transcript = transcribe(client, ab)
                    stt_ms = int((time.time() - t0) * 1000)
                if not transcript:
                    st.session_state.processing = False
                    st.error("No speech detected."); st.stop()
        elif text_value.strip():
            transcript = text_value.strip()
        if not transcript:
            st.session_state.processing = False
            st.info("Speak or type a question."); st.stop()

        st.session_state.last_transcript = transcript
        st.session_state.history.append({"role": "user", "content": transcript})

        with st.spinner("Thinking..."):
            resp, timing = generate_response(client, transcript, class_level, subject, temperature, max_tokens)
        if not resp:
            st.session_state.processing = False
            st.error("Failed."); st.stop()
        timing["stt_ms"] = stt_ms

        audio_b64 = None
        if voice_id:
            with st.spinner("Generating speech..."):
                audio_b64, tts_ms = synthesize_speech(client, resp.audio_speech, voice_id)
                timing["tts_ms"] = tts_ms

        timing["total_ms"] = sum(v for v in timing.values() if isinstance(v, int))

        st.session_state.last_response = resp
        st.session_state.last_audio = audio_b64
        st.session_state.last_timing = timing
        st.session_state.last_words = []
        st.session_state.status = "speaking"
        st.session_state.history.append({"role": "assistant", "content": resp.audio_speech[:200]})
        st.session_state.processing = False
        st.rerun()

    # Response
    if st.session_state.last_response:
        resp = st.session_state.last_response
        words = st.session_state.get("last_words", [])

        if st.session_state.last_transcript:
            st.markdown(f'<div class="transcript-box"><div style="color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:4px;">Transcript</div><div style="color:var(--text);font-size:15px;">{st.session_state.last_transcript}</div></div>', unsafe_allow_html=True)

        # Audio + Karaoke Captions
        if st.session_state.last_audio:
            if words:
                render_karaoke_captions(st.session_state.last_audio, words, resp.audio_speech)
            else:
                # Fallback: basic audio player when no word timestamps
                st.audio(base64.b64decode(st.session_state.last_audio), format="audio/mp3", autoplay=True)
                if resp.audio_speech:
                    st.markdown(f"""
                    <div style="background:var(--glass);border:1px solid var(--glass-border);border-radius:14px;padding:20px;margin:12px 0;">
                        <div style="color:var(--primary);font-size:10px;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;">Spoken Text</div>
                        <div style="color:var(--text);font-size:15px;line-height:1.8;">{resp.audio_speech}</div>
                    </div>
                    """, unsafe_allow_html=True)

        c_resp, c_board = st.columns([3, 2])
        with c_resp:
            if resp.mode == "SIMPLIFY": render_simplify(resp)
            elif resp.mode == "QUIZ": render_quiz(resp)
            elif resp.mode == "TRANSLATE": render_translation(resp)
            elif resp.mode == "ACTIVITY": render_activity(resp)
            render_timing(st.session_state.last_timing)

        with c_board:
            st.markdown('<div class="section-label">Smart Board</div>', unsafe_allow_html=True)
            render_smart_board(resp)

        # Export Button
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        export_html = generate_export_html(resp, st.session_state.last_transcript, st.session_state.last_audio, words)
        st.download_button(
            label="Export HTML",
            data=export_html,
            file_name=f"classroom-copilot-{resp.mode.lower()}.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )

    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🎓</div>
            <div class="empty-title">Ready to teach?</div>
            <div class="empty-sub">Speak or type a question to get started.<br>Try the quick examples in the sidebar.</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
