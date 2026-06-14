import base64
import os
import time

import streamlit as st
from dotenv import load_dotenv

from lib.client import get_client, transcribe, generate_response, synthesize_speech

load_dotenv()

st.set_page_config(page_title="Classroom Co-Pilot AI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════
# CUSTOM CSS — Dark glass-morphism for smart board
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

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
.main-header p { color: rgba(255,255,255,0.5); margin: 4px 0 0; font-size: 14px; }

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
    font-size: 15px;
    line-height: 1.5;
}
.point-card strong { color: #00d4aa; }

/* Quiz */
.quiz-option {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    color: rgba(255,255,255,0.7);
    font-size: 15px;
    transition: all 0.2s;
}
.quiz-option.correct { border-color: #34d399; background: rgba(52,211,153,0.1); color: #34d399; }
.quiz-option.incorrect { border-color: #ef4444; background: rgba(239,68,68,0.1); color: #ef4444; }

/* Translation */
.trans-card {
    background: rgba(124,58,237,0.06);
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
}
.trans-original { color: rgba(255,255,255,0.5); font-size: 13px; margin-bottom: 8px; }
.trans-translated { color: white; font-size: 18px; font-weight: 600; }

/* Activity Timer */
.timer-box {
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.2);
    border-radius: 14px;
    padding: 24px;
    text-align: center;
}
.timer-time { font-size: 48px; font-weight: 800; color: #fbbf24; font-variant-numeric: tabular-nums; }
.timer-step { color: rgba(255,255,255,0.7); font-size: 15px; margin: 8px 0; }
.timer-step.active { color: #fbbf24; font-weight: 600; }

/* Timing badges */
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
.status-pill { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.status-idle { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.4); }
.status-processing { background: rgba(251,191,36,0.15); color: #fbbf24; }
.status-speaking { background: rgba(0,212,170,0.15); color: #00d4aa; }
.status-error { background: rgba(239,68,68,0.15); color: #ef4444; }

/* Sidebar */
section[data-testid="stSidebar"] { background: rgba(13,17,23,0.95); border-right: 1px solid rgba(255,255,255,0.06); }

/* Feature pills */
.feature-pill {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin: 3px;
    border: 1px solid;
}
.feature-simplify { background: rgba(0,212,170,0.1); border-color: rgba(0,212,170,0.25); color: #00d4aa; }
.feature-quiz { background: rgba(124,58,237,0.1); border-color: rgba(124,58,237,0.25); color: #a78bfa; }
.feature-translate { background: rgba(59,130,246,0.1); border-color: rgba(59,130,246,0.25); color: #60a5fa; }
.feature-activity { background: rgba(251,191,36,0.1); border-color: rgba(251,191,36,0.25); color: #fbbf24; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def init_session():
    for k, v in {
        "history": [], "status": "idle", "last_response": None, "last_audio": None,
        "last_transcript": "", "last_timing": {}, "quiz_score": {"correct": 0, "total": 0},
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_header():
    s = st.session_state.status
    st.markdown(f"""
    <div class="main-header">
        <h1>Classroom Co-Pilot AI</h1>
        <p>Voice-First AI Teaching Assistant for Haryana Government Schools &nbsp;
            <span class="status-pill status-{s}">{s.upper()}</span>
        </p>
        <div style="margin-top:8px">
            <span class="feature-pill feature-simplify">Live Explanation</span>
            <span class="feature-pill feature-quiz">Voice Quizzes</span>
            <span class="feature-pill feature-translate">Translation</span>
            <span class="feature-pill feature-activity">Activity Guide</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### Settings")
        api_key = st.text_input("Mistral API Key", value=os.getenv("MISTRAL_API_KEY", ""), type="password",
                                help="Get yours at console.mistral.ai")
        if api_key: os.environ["MISTRAL_API_KEY"] = api_key

        class_level = st.selectbox("Class Level", ["", "6", "7", "8", "9", "10"],
                                   format_func=lambda x: f"Class {x}" if x else "Auto-detect")
        subject = st.selectbox("Subject Focus", ["auto", "Science", "Mathematics"])
        voice_id = st.selectbox("Voice", [
            "en_paul_neutral", "en_oliver_confident", "en_jane_neutral",
            "en_marie_confident", "gb_jane_confident", "gb_geoffrey_confident",
        ], help="Mistral preset voice for TTS")

        st.divider()
        st.markdown("### History")
        if st.session_state.history:
            for entry in reversed(st.session_state.history[-8:]):
                icon = "🎙" if entry["role"] == "user" else "🤖"
                text = entry["content"][:80] + ("..." if len(entry["content"]) > 80 else "")
                st.markdown(f"{icon} {text}")
            if st.button("Clear History"): st.session_state.history = []; st.rerun()
        else:
            st.caption("No conversations yet.")

        # Score display
        if st.session_state.quiz_score["total"] > 0:
            sc = st.session_state.quiz_score
            st.divider()
            st.markdown(f"### Quiz Score: {sc['correct']}/{sc['total']}")

    return api_key, class_level, subject, voice_id


def render_simplify(response):
    if not response.screen_data: return
    sd = response.screen_data
    st.markdown(f"### {sd.title}")
    for i, p in enumerate(sd.points):
        st.markdown(f'<div class="point-card"><strong>{i+1}.</strong> {p}</div>', unsafe_allow_html=True)
    if sd.visual_cue:
        st.markdown(f"""<div style="margin-top:12px;padding:12px;background:rgba(0,212,170,0.05);
            border:1px solid rgba(0,212,170,0.15);border-radius:10px;
            color:rgba(255,255,255,0.5);font-size:13px;font-style:italic;">
            Visual: {sd.visual_cue}</div>""", unsafe_allow_html=True)


def render_quiz(response):
    if not response.quiz_data: return
    qd = response.quiz_data
    st.markdown(f"### Quiz: {qd.topic}")

    for qi, q in enumerate(qd.questions):
        st.markdown(f'<div style="margin:16px 0 8px;color:rgba(255,255,255,0.85);font-size:16px;font-weight:600;">Q{qi+1}. {q.question}</div>', unsafe_allow_html=True)
        selected = st.radio("Answer", q.options, key=f"quiz_{qi}", label_visibility="collapsed")
        idx = q.options.index(selected) if selected in q.options else -1
        if idx == q.correct_index:
            st.markdown('<div class="quiz-option correct">Correct!</div>', unsafe_allow_html=True)
            if not st.session_state.get(f"quiz_counted_{qi}"):
                st.session_state.quiz_score["correct"] += 1
                st.session_state.quiz_score["total"] += 1
                st.session_state[f"quiz_counted_{qi}"] = True
        elif idx != -1:
            st.markdown(f'<div class="quiz-option incorrect">Incorrect. Correct answer: {q.options[q.correct_index]}</div>', unsafe_allow_html=True)
            if not st.session_state.get(f"quiz_counted_{qi}"):
                st.session_state.quiz_score["total"] += 1
                st.session_state[f"quiz_counted_{qi}"] = True


def render_translation(response):
    if not response.translation: return
    t = response.translation
    st.markdown(f"""
    <div class="trans-card">
        <div class="trans-original">{t.get('original', '')}</div>
        <div class="trans-translated">{t.get('translated', '')}</div>
        <div style="color:rgba(255,255,255,0.3);font-size:12px;margin-top:8px;">{t.get('language', '')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_activity(response):
    if not response.activity: return
    a = response.activity
    duration = a.get("duration_seconds", 300)
    steps = a.get("steps", [])

    st.markdown(f"### Activity: {a.get('instruction', '')}")

    # Timer
    timer_placeholder = st.empty()
    if st.button("Start Timer", type="primary"):
        for remaining in range(duration, 0, -1):
            mins, secs = divmod(remaining, 60)
            active_step = len(steps) - 1 if steps else 0
            for si, s in enumerate(steps):
                step_duration = duration / len(steps)
                if remaining > duration - step_duration * (si + 1):
                    active_step = si
                    break

            steps_html = "".join(
                f'<div class="timer-step {"active" if i == active_step else ""}">{i+1}. {s}</div>'
                for i, s in enumerate(steps)
            )
            timer_placeholder.markdown(f"""
            <div class="timer-box">
                <div class="timer-time">{mins:02d}:{secs:02d}</div>
                {steps_html}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
        timer_placeholder.markdown("""<div class="timer-box">
            <div class="timer-time" style="color:#34d399;">DONE!</div>
            <div class="timer-step" style="color:#34d399;">Activity completed!</div>
        </div>""", unsafe_allow_html=True)
    else:
        mins, secs = divmod(duration, 60)
        steps_html = "".join(f'<div class="timer-step">{i+1}. {s}</div>' for i, s in enumerate(steps))
        timer_placeholder.markdown(f"""<div class="timer-box">
            <div class="timer-time">{mins:02d}:{secs:02d}</div>
            {steps_html}
        </div>""", unsafe_allow_html=True)


def render_timing(timing: dict):
    badges = []
    for key, label in [("stt_ms","STT"),("llm_ms","LLM"),("tts_ms","TTS"),("total_ms","Total")]:
        if key in timing and timing[key]: badges.append(f"{label}: {timing[key]}ms")
    if badges:
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

    col_main, col_right = st.columns([3, 2])

    with col_main:
        st.markdown("### Ask a Question")

        audio_value = st.audio_input("Record your question", key="audio")
        text_value = st.text_input("Or type your question", placeholder="e.g. Photosynthesis samjhao / Translate this / Newton's laws quiz lagao...", key="text")

        if st.button("Ask", type="primary", use_container_width=True):
            transcript = ""
            if audio_value is not None:
                audio_bytes = audio_value.getvalue()
                if audio_bytes:
                    with st.spinner("Transcribing..."):
                        t0 = time.time()
                        transcript = transcribe(client, audio_bytes)
                        stt_ms = int((time.time() - t0) * 1000)
                    if not transcript:
                        st.error("No speech detected."); st.stop()
            elif text_value.strip():
                transcript = text_value.strip()

            if not transcript:
                st.info("Ask a question by voice or text."); st.stop()

            st.session_state.last_transcript = transcript
            st.session_state.history.append({"role": "user", "content": transcript})

            with st.spinner("Thinking..."):
                response, timing = generate_response(client, transcript, class_level, subject)
            if not response:
                st.error("Failed to generate response."); st.stop()
            timing["stt_ms"] = stt_ms if audio_value else 0

            audio_b64 = None
            if voice_id:
                with st.spinner("Generating speech..."):
                    audio_b64, tts_ms = synthesize_speech(client, response.audio_speech, voice_id)
                    timing["tts_ms"] = tts_ms
            timing["total_ms"] = sum(v for v in timing.values() if isinstance(v, int))

            st.session_state.last_response = response
            st.session_state.last_audio = audio_b64
            st.session_state.last_timing = timing
            st.session_state.status = "speaking"
            st.session_state.history.append({"role": "assistant", "content": response.audio_speech[:200]})
            st.rerun()

        # ─── Display response ───
        if st.session_state.last_response:
            response = st.session_state.last_response
            st.divider()

            if st.session_state.last_transcript:
                st.markdown(f"""<div class="glass-card">
                    <div style="color:rgba(255,255,255,0.4);font-size:11px;margin-bottom:4px;">TRANSCRIPT</div>
                    <div style="color:rgba(255,255,255,0.8);font-size:15px;">{st.session_state.last_transcript}</div>
                </div>""", unsafe_allow_html=True)

            if st.session_state.last_audio:
                st.audio(base64.b64decode(st.session_state.last_audio), format="audio/mp3", autoplay=True)

            if response.mode == "SIMPLIFY": render_simplify(response)
            elif response.mode == "QUIZ": render_quiz(response)
            elif response.mode == "TRANSLATE": render_translation(response)
            elif response.mode == "ACTIVITY": render_activity(response)

            render_timing(st.session_state.last_timing)

    # ─── Smart Board Right Panel ───
    with col_right:
        st.markdown("### Smart Board Display")

        if st.session_state.last_response:
            response = st.session_state.last_response
            if response.mode == "SIMPLIFY" and response.screen_data:
                sd = response.screen_data
                st.markdown(f"""<div style="background:rgba(0,212,170,0.06);border:1px solid rgba(0,212,170,0.15);
                    border-radius:14px;padding:24px;text-align:center;min-height:300px;
                    display:flex;flex-direction:column;justify-content:center;align-items:center;">
                    <h2 style="color:white;margin:0 0 16px;font-size:22px;">{sd.title}</h2>
                    {''.join(f'<div style="text-align:left;width:100%;padding:8px 16px;margin:4px 0;background:rgba(255,255,255,0.04);border-radius:8px;color:rgba(255,255,255,0.6);font-size:14px;"><strong style="color:#00d4aa">{i+1}.</strong> {p}</div>' for i, p in enumerate(sd.points))}
                    <div style="margin-top:16px;color:rgba(255,255,255,0.3);font-size:12px;font-style:italic;">{sd.visual_cue}</div>
                </div>""", unsafe_allow_html=True)

            elif response.mode == "QUIZ" and response.quiz_data:
                qd = response.quiz_data
                st.markdown(f"### Quiz: {qd.topic}")
                for qi, q in enumerate(qd.questions):
                    st.markdown(f"""<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:16px;margin:10px 0;">
                        <div style="color:rgba(255,255,255,0.85);font-weight:600;margin-bottom:8px;">Q{qi+1}. {q.question}</div>
                        {''.join(f'<div style="padding:6px 12px;margin:3px 0;border-radius:6px;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.5);font-size:13px;">{chr(65+j)}. {opt}</div>' for j, opt in enumerate(q.options))}
                    </div>""", unsafe_allow_html=True)

            elif response.mode == "TRANSLATE" and response.translation:
                t = response.translation
                st.markdown(f"""<div style="background:rgba(124,58,237,0.06);border:1px solid rgba(124,58,237,0.2);
                    border-radius:14px;padding:24px;text-align:center;min-height:300px;
                    display:flex;flex-direction:column;justify-content:center;align-items:center;">
                    <div style="color:rgba(255,255,255,0.4);font-size:12px;margin-bottom:8px;">ORIGINAL</div>
                    <div style="color:rgba(255,255,255,0.6);font-size:16px;margin-bottom:24px;">{t.get('original','')}</div>
                    <div style="color:rgba(255,255,255,0.2);font-size:24px;margin-bottom:24px;">↕</div>
                    <div style="color:rgba(255,255,255,0.4);font-size:12px;margin-bottom:8px;">TRANSLATED</div>
                    <div style="color:white;font-size:22px;font-weight:700;">{t.get('translated','')}</div>
                    <div style="color:rgba(255,255,255,0.3);font-size:12px;margin-top:16px;">{t.get('language','')}</div>
                </div>""", unsafe_allow_html=True)

            elif response.mode == "ACTIVITY" and response.activity:
                a = response.activity
                steps_html = "".join(f'<div style="padding:8px 12px;margin:4px 0;background:rgba(255,255,255,0.04);border-radius:8px;color:rgba(255,255,255,0.6);font-size:14px;"><strong style="color:#fbbf24">{i+1}.</strong> {s}</div>' for i, s in enumerate(a.get("steps", [])))
                st.markdown(f"""<div style="background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.15);
                    border-radius:14px;padding:24px;min-height:300px;">
                    <h3 style="color:#fbbf24;margin:0 0 8px;">Activity Guide</h3>
                    <div style="color:rgba(255,255,255,0.6);font-size:14px;margin-bottom:16px;">{a.get('instruction','')}</div>
                    <div style="color:rgba(255,255,255,0.4);font-size:12px;margin-bottom:8px;">Duration: {a.get('duration_seconds',0)//60} min {a.get('duration_seconds',0)%60} sec</div>
                    {steps_html}
                </div>""", unsafe_allow_html=True)

        else:
            st.markdown("""<div style="background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.08);
                border-radius:14px;padding:60px 24px;text-align:center;min-height:300px;
                display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="font-size:48px;margin-bottom:16px;opacity:0.3;">🎓</div>
                <div style="color:rgba(255,255,255,0.3);font-size:14px;">
                    Ask a question to see visuals on the smart board<br><br>
                    <span style="font-size:12px;color:rgba(255,255,255,0.2);">
                    Try: "Photosynthesis samjhao" | "Quiz lagao" | "Translate this" | "Activity guide do"</span>
                </div>
            </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
