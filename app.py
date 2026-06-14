import base64
import os
import time

import streamlit as st
from dotenv import load_dotenv

from lib.client import get_client, transcribe, generate_response, synthesize_speech

load_dotenv()

# ─── Page Config ───
st.set_page_config(
    page_title="Classroom Co-Pilot AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Dark glass background */
.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1117 40%, #0a0a1a 100%);
    font-family: 'Inter', sans-serif;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, rgba(0,212,170,0.12), rgba(124,58,237,0.12));
    border: 1px solid rgba(0,212,170,0.15);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 20px;
    backdrop-filter: blur(20px);
}
.main-header h1 {
    color: white !important;
    font-size: 28px;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.main-header p {
    color: rgba(255,255,255,0.5);
    margin: 4px 0 0;
    font-size: 14px;
}

/* Glass card */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px;
    backdrop-filter: blur(12px);
    margin-bottom: 16px;
}

/* Point cards */
.point-card {
    background: rgba(255,255,255,0.03);
    border-left: 3px solid #00d4aa;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
    color: rgba(255,255,255,0.7);
    font-size: 14px;
    line-height: 1.5;
}
.point-card strong {
    color: #00d4aa;
}

/* Quiz options */
.quiz-option {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    color: rgba(255,255,255,0.7);
    font-size: 14px;
    transition: all 0.2s;
}
.quiz-option:hover {
    border-color: rgba(0,212,170,0.3);
    background: rgba(0,212,170,0.05);
}
.quiz-option.correct {
    border-color: #34d399;
    background: rgba(52,211,153,0.1);
    color: #34d399;
}
.quiz-option.incorrect {
    border-color: #ef4444;
    background: rgba(239,68,68,0.1);
    color: #ef4444;
}

/* Timing badge */
.timing-badge {
    display: inline-block;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    color: rgba(255,255,255,0.4);
    margin: 2px;
}

/* Status pill */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.status-idle { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.4); }
.status-processing { background: rgba(251,191,36,0.15); color: #fbbf24; }
.status-speaking { background: rgba(0,212,170,0.15); color: #00d4aa; }
.status-error { background: rgba(239,68,68,0.15); color: #ef4444; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(13,17,23,0.95);
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def init_session():
    defaults = {
        "history": [],
        "status": "idle",
        "last_response": None,
        "last_audio": None,
        "last_transcript": "",
        "last_timing": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_header():
    status = st.session_state.status
    pill_class = f"status-{status}"
    pill_label = status.upper()
    st.markdown(f"""
    <div class="main-header">
        <h1>Classroom Co-Pilot AI</h1>
        <p>Voice-First AI Teaching Assistant for Smart Classrooms &nbsp;
            <span class="status-pill {pill_class}">{pill_label}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### Settings")

        api_key = st.text_input(
            "Mistral API Key",
            value=os.getenv("MISTRAL_API_KEY", ""),
            type="password",
            help="Get yours at console.mistral.ai",
        )
        if api_key:
            os.environ["MISTRAL_API_KEY"] = api_key

        class_level = st.selectbox(
            "Class Level",
            ["", "6", "7", "8", "9", "10"],
            format_func=lambda x: f"Class {x}" if x else "Auto-detect",
        )

        subject = st.selectbox(
            "Subject Focus",
            ["auto", "Science", "Mathematics"],
        )

        voice_id = st.selectbox(
            "Voice",
            [
                "en_paul_neutral",
                "en_oliver_confident",
                "en_jane_neutral",
                "en_marie_confident",
                "gb_jane_confident",
                "gb_geoffrey_confident",
                "fr_antoine_confident",
                "de_karl_confident",
            ],
            help="Mistral preset voice for TTS",
        )

        st.divider()
        st.markdown("### Conversation History")

        if st.session_state.history:
            for i, entry in enumerate(reversed(st.session_state.history[-10:])):
                role = "Teacher" if entry["role"] == "user" else "AI"
                text = entry["content"][:80] + ("..." if len(entry["content"]) > 80 else "")
                st.markdown(f"**{role}:** {text}")
        else:
            st.caption("No conversations yet. Speak or type to start!")

        if st.session_state.history:
            if st.button("Clear History", type="secondary"):
                st.session_state.history = []
                st.rerun()

    return api_key, class_level, subject, voice_id


def render_simplify(response):
    if not response.screen_data:
        st.info("No screen data available.")
        return

    sd = response.screen_data

    # Title
    st.markdown(f"### {sd.title}")

    # Points
    for i, point in enumerate(sd.points):
        st.markdown(f"""
        <div class="point-card">
            <strong>{i+1}.</strong> {point}
        </div>
        """, unsafe_allow_html=True)

    # Visual cue
    if sd.visual_cue:
        st.markdown(f"""
        <div style="margin-top:12px;padding:12px;background:rgba(0,212,170,0.05);
             border:1px solid rgba(0,212,170,0.15);border-radius:10px;
             color:rgba(255,255,255,0.5);font-size:13px;font-style:italic;">
            Visual: {sd.visual_cue}
        </div>
        """, unsafe_allow_html=True)


def render_quiz(response):
    if not response.quiz_data:
        st.info("No quiz data available.")
        return

    qd = response.quiz_data
    st.markdown(f"### Quiz: {qd.topic}")

    for qi, q in enumerate(qd.questions):
        st.markdown(f"""
        <div style="margin:16px 0 8px;color:rgba(255,255,255,0.85);font-size:15px;font-weight:600;">
            Q{qi+1}. {q.question}
        </div>
        """, unsafe_allow_html=True)

        # Use radio for selection
        selected = st.radio(
            "Select answer",
            q.options,
            key=f"quiz_q_{qi}",
            label_visibility="collapsed",
        )

        selected_idx = q.options.index(selected) if selected in q.options else -1
        if selected_idx == q.correct_index:
            st.markdown('<div class="quiz-option correct">Correct!</div>', unsafe_allow_html=True)
        elif selected_idx != -1:
            st.markdown(
                f'<div class="quiz-option incorrect">Incorrect. Correct answer: {q.options[q.correct_index]}</div>',
                unsafe_allow_html=True,
            )


def render_timing(timing: dict):
    if not timing:
        return
    badges = []
    if "stt_ms" in timing and timing["stt_ms"]:
        badges.append(f"STT: {timing['stt_ms']}ms")
    if "llm_ms" in timing and timing["llm_ms"]:
        badges.append(f"LLM: {timing['llm_ms']}ms")
    if "tts_ms" in timing and timing["tts_ms"]:
        badges.append(f"TTS: {timing['tts_ms']}ms")
    if "total_ms" in timing and timing["total_ms"]:
        badges.append(f"Total: {timing['total_ms']}ms")

    html = " ".join(f'<span class="timing-badge">{b}</span>' for b in badges)
    st.markdown(f'<div style="margin-top:12px">{html}</div>', unsafe_allow_html=True)


def main():
    init_session()
    render_header()
    api_key, class_level, subject, voice_id = render_sidebar()

    if not api_key:
        st.warning("Enter your Mistral API key in the sidebar to start.")
        st.stop()

    client = get_client(api_key)

    # ─── Main content area ───
    col_main, col_right = st.columns([3, 2])

    with col_main:
        st.markdown("### Speak or Type")

        # Audio input
        audio_value = st.audio_input("Record your question", key="audio_input")

        # Text input fallback
        text_value = st.text_input(
            "Or type your question",
            placeholder="e.g. Photosynthesis samjhao...",
            key="text_input",
        )

        # Submit button
        if st.button("Ask", type="primary", use_container_width=True):
            transcript = ""

            if audio_value is not None:
                audio_bytes = audio_value.getvalue()
                if audio_bytes:
                    st.session_state.status = "processing"
                    st.rerun()

                    with st.spinner("Transcribing..."):
                        t0 = time.time()
                        transcript = transcribe(client, audio_bytes)
                        stt_ms = int((time.time() - t0) * 1000)

                    if not transcript:
                        st.error("No speech detected. Please try again.")
                        st.stop()
            elif text_value.strip():
                transcript = text_value.strip()

            if not transcript:
                st.info("Ask a question by voice or text.")
                st.stop()

            # Store transcript
            st.session_state.last_transcript = transcript
            st.session_state.history.append({"role": "user", "content": transcript})

            # Generate response
            with st.spinner("Thinking..."):
                response, timing = generate_response(client, transcript, class_level, subject)

            if not response:
                st.error("Failed to generate response. Please try again.")
                st.session_state.status = "error"
                st.stop()

            timing["stt_ms"] = stt_ms if audio_value else 0

            # TTS
            audio_b64 = None
            if voice_id:
                with st.spinner("Generating speech..."):
                    audio_b64, tts_ms = synthesize_speech(client, response.audio_speech, voice_id)
                    timing["tts_ms"] = tts_ms

            timing["total_ms"] = sum(v for v in timing.values() if isinstance(v, int))

            # Store response
            st.session_state.last_response = response
            st.session_state.last_audio = audio_b64
            st.session_state.last_timing = timing
            st.session_state.status = "speaking"

            # Add to history
            st.session_state.history.append({
                "role": "assistant",
                "content": response.audio_speech[:200],
            })

            st.rerun()

        # ─── Display current response ───
        if st.session_state.last_response:
            response = st.session_state.last_response

            st.divider()

            # Transcript
            if st.session_state.last_transcript:
                st.markdown(f"""
                <div class="glass-card">
                    <div style="color:rgba(255,255,255,0.4);font-size:11px;margin-bottom:4px;">TRANSCRIPT</div>
                    <div style="color:rgba(255,255,255,0.8);font-size:15px;">
                        {st.session_state.last_transcript}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Audio playback
            if st.session_state.last_audio:
                audio_bytes = base64.b64decode(st.session_state.last_audio)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            # Response content
            if response.mode == "SIMPLIFY":
                render_simplify(response)
            elif response.mode == "QUIZ":
                render_quiz(response)

            # Timing
            render_timing(st.session_state.last_timing)

    with col_right:
        st.markdown("### Smart Board")

        if st.session_state.last_response:
            response = st.session_state.last_response
            if response.mode == "SIMPLIFY" and response.screen_data:
                sd = response.screen_data
                st.markdown(f"""
                <div style="background:rgba(0,212,170,0.06);border:1px solid rgba(0,212,170,0.15);
                     border-radius:14px;padding:24px;text-align:center;min-height:300px;
                     display:flex;flex-direction:column;justify-content:center;align-items:center;">
                    <div style="font-size:32px;margin-bottom:12px;">
                        {' '.join(['💡','🔬','📐','⚡','🌱','🌊','☀️'][:min(len(sd.points), 7)])
                        if not sd.visual_cue else ''}
                    </div>
                    <h2 style="color:white;margin:0 0 16px;font-size:22px;">{sd.title}</h2>
                    {''.join(f'<div style="text-align:left;width:100%;padding:8px 16px;margin:4px 0;'
                    f'background:rgba(255,255,255,0.04);border-radius:8px;color:rgba(255,255,255,0.6);'
                    f'font-size:14px;"><strong style="color:#00d4aa">{i+1}.</strong> {p}</div>'
                    for i, p in enumerate(sd.points))}
                    <div style="margin-top:16px;color:rgba(255,255,255,0.3);font-size:12px;
                         font-style:italic;">{sd.visual_cue}</div>
                </div>
                """, unsafe_allow_html=True)

            elif response.mode == "QUIZ" and response.quiz_data:
                st.markdown(f"### Quiz: {response.quiz_data.topic}")
                for qi, q in enumerate(response.quiz_data.questions):
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:16px;margin:10px 0;">
                        <div style="color:rgba(255,255,255,0.85);font-weight:600;margin-bottom:8px;">
                            Q{qi+1}. {q.question}
                        </div>
                        {''.join(f'<div style="padding:6px 12px;margin:3px 0;border-radius:6px;'
                        f'background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.5);font-size:13px;">'
                        f'{chr(65+j)}. {opt}</div>' for j, opt in enumerate(q.options))}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.08);
                 border-radius:14px;padding:60px 24px;text-align:center;min-height:300px;
                 display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="font-size:48px;margin-bottom:16px;opacity:0.3;">🎓</div>
                <div style="color:rgba(255,255,255,0.3);font-size:14px;">
                    Ask a question to see visuals on the smart board
                </div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
