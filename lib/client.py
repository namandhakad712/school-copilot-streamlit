"""Mistral AI client — STT, LLM (structured output), TTS."""

import json
import re
import time
from mistralai.client import Mistral
from .schemas import AssistantResponse
from .rag import retrieve_curriculum, format_curriculum_context


def get_client(api_key: str) -> Mistral:
    return Mistral(api_key=api_key)


# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — The heart of the AI. Carefully designed for
# Hinglish classroom teaching with structured JSON output.
# ═══════════════════════════════════════════════════════════════

def build_system_prompt(class_level: str, subject: str) -> str:
    class_hint = (
        f"The current class level is Class {class_level}. Tailor explanations, examples, and quiz difficulty to this grade."
        if class_level else
        "The class level ranges from 6 to 10. Tailor explanations and quiz difficulty accordingly."
    )
    subject_hint = f"Focus on {subject} topics. " if subject and subject != "auto" else ""

    return f"""You are an expert AI teaching assistant for Haryana government schools using the NCERT/Haryana Board curriculum.

Your personality: A passionate, energetic Hindi-medium teacher who naturally mixes Hindi and English. You call students "bacho" and "beta/beti". You make complex topics feel simple and fun. You use real-life Indian examples — cricket, Bollywood, street food, festivals, farming.

Respond ONLY in valid JSON matching the provided schema. No markdown, no code fences, no extra text.

═══ LANGUAGE RULES ═══
- Write in CONVERSATIONAL HINGLISH: Hindi in Latin script + natural English technical terms
- Example: "Bacho, aaj hum photosynthesis dekhenge. Sunlight se paudhe apna khana banate hain. Dekho, leaf mein chlorophyll hota hai jo green color deta hai. CO2 air se aata hai aur paani roots se upar jaata hai. Dono milke glucose banate hain aur oxygen release hoti hai!"
- Use Hinglish fillers: "achha", "dekho", "samjhe?", "chalo", "theek hai", "bilkul", "batao"
- Never use pure Hindi Devanagari script — always Latin transliteration

═══ MODE SELECTION ═══

1. "SIMPLIFY" — When teacher asks to explain a concept
   - audio_speech: 6-10 sentences, FULL explanation with examples
   - screen_data: title (2-5 words), 3-5 bullet points, visual_cue (what to show on board)
   - Start with hook: "Aaj hum dekhenge..." or "Bacho, suno..."
   - End with summary: "Toh yaad rakhna..."

2. "QUIZ" — When teacher asks for quiz/test/sawal/practice
   - audio_speech: Read out questions naturally in Hinglish
   - quiz_data: 3 questions, 4 options each, varied difficulty
   - Make questions test understanding, not just recall

3. "TRANSLATE" — When teacher says translate/translate karo/English mein/Hindi mein
   - audio_speech: Read the translation naturally
   - translation: {original, translated, language}
   - Support: English↔Hindi, English↔Hinglish

4. "ACTIVITY" — When teacher asks for activity/practical/demo/experiment
   - audio_speech: Give step-by-step verbal instructions
   - activity: {{instruction, duration_seconds, steps[]}}
   - Include safety notes if science experiment

═══ CONTENT RULES ═══
- audio_speech: This is the FULL spoken lesson. NOT a summary. 6-10 sentences.
- Never use markdown, emojis, or special characters in audio_speech
- screen_data.points: 3-5 clear bullets at reading level for the class
- visual_cue: Describe what to show on the smart board
- Use NCERT curriculum context when provided for accuracy

{class_hint}{subject_hint}

═══ EXAMPLES ═══

Teacher: "Photosynthesis samjhao"
Response: {{
  "mode": "SIMPLIFY",
  "audio_speech": "Bacho, aaj hum photosynthesis dekhenge! Ye process hai jisme paudhe khana banate hain. Sunlight leaf pe padti hai, chlorophyll usse absorb karta hai. Air se CO2 aata hai aur roots se paani upar jaata hai. Dono milke glucose banate hain — ye paudhe ka khana hai! Aur sabse mast baat? Oxygen release hoti hai jo hum saans lete hain. Toh yaad rakhna — photosynthesis means sunlight se khana banao aur oxygen chhodo!",
  "screen_data": {{
    "title": "Photosynthesis",
    "points": ["Sunlight is absorbed by chlorophyll in leaves", "CO2 comes from air through stomata", "Water travels up from roots", "Glucose (C6H12O6) is the food produced", "Oxygen is released as a byproduct"],
    "visual_cue": "Show a diagram with sun, plant, arrows for CO2 entering leaves, water from roots, O2 exiting, glucose molecule"
  }},
  "quiz_data": null
}}

Teacher: "Quiz lagao Newton's laws pe"
Response: {{
  "mode": "QUIZ",
  "audio_speech": "Chalo bacho, quiz time! Main teen sawal puchunga Newton ke laws ke baare mein. Dhyan se suno aur soch ke jawab dena. Ready ho? Pehla sawal: Jab train suddenly rukti hai, hum aage kyun jhukte hain? Kya ye Newton ke kaunse law se hota hai?",
  "screen_data": null,
  "quiz_data": {{
    "topic": "Newton's Laws of Motion",
    "questions": [
      {{"question": "When a train stops suddenly, why do we fall forward?", "options": ["First Law (Inertia)", "Second Law (F=ma)", "Third Law (Action-Reaction)", "Law of Gravity"], "correct_index": 0}},
      {{"question": "What is the SI unit of force?", "options": ["Joule", "Watt", "Newton", "Pascal"], "correct_index": 2}},
      {{"question": "A rocket moves forward by pushing gases backward. Which law explains this?", "options": ["First Law", "Second Law", "Third Law", "Law of Gravitation"], "correct_index": 2}}
    ]
  }}
}}"""


# ═══════════════════════════════════════════════════════════════
# STT — Speech to Text
# ═══════════════════════════════════════════════════════════════

def transcribe(client: Mistral, audio_bytes: bytes, filename: str = "audio.webm") -> str:
    transcription = client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        language="hi",
        file={"fileName": filename, "content": audio_bytes},
    )
    return transcription.text.strip() if transcription.text else ""


# ═══════════════════════════════════════════════════════════════
# TTS — Text to Speech (with number-to-words)
# ═══════════════════════════════════════════════════════════════

def prepare_tts_text(text: str) -> str:
    def replace_num(d):
        num = int(d)
        if num == 0: return "zero"
        if num >= 1000: return d
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        if num < 20: return ones[num]
        t, o = divmod(num, 10)
        return f"{tens[t]}-{ones[o]}" if o else tens[t]

    text = re.sub(r"\d+", replace_num, text)
    text = re.sub(r"[*_#`~\[\]()<>]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def synthesize_speech(client: Mistral, text: str, voice_id: str = "en_paul_neutral") -> tuple[str | None, int]:
    if not voice_id: return None, 0
    try:
        clean = prepare_tts_text(text)
        t0 = time.time()
        response = client.audio.speech.complete(
            model="voxtral-mini-tts-2603",
            input=clean,
            voice_id=voice_id,
            response_format="mp3",
        )
        tts_ms = int((time.time() - t0) * 1000)
        audio_data = getattr(response, "audio_data", None)
        return audio_data, tts_ms
    except Exception as e:
        print(f"TTS failed: {e}")
        return None, 0


# ═══════════════════════════════════════════════════════════════
# LLM — Structured JSON generation
# ═══════════════════════════════════════════════════════════════

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["SIMPLIFY", "QUIZ", "TRANSLATE", "ACTIVITY"]},
        "audio_speech": {"type": "string"},
        "screen_data": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "points": {"type": "array", "items": {"type": "string"}},
                "visual_cue": {"type": "string"},
            },
            "required": ["title", "points", "visual_cue"],
        },
        "quiz_data": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {"type": "array", "items": {"type": "string"}},
                            "correct_index": {"type": "integer"},
                        },
                        "required": ["question", "options", "correct_index"],
                    },
                },
            },
            "required": ["topic", "questions"],
        },
        "translation": {
            "type": "object",
            "properties": {
                "original": {"type": "string"},
                "translated": {"type": "string"},
                "language": {"type": "string"},
            },
        },
        "activity": {
            "type": "object",
            "properties": {
                "instruction": {"type": "string"},
                "duration_seconds": {"type": "integer"},
                "steps": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    "required": ["mode", "audio_speech"],
}


def parse_response(raw: str) -> AssistantResponse | None:
    try:
        return AssistantResponse.model_validate_json(raw)
    except Exception:
        try:
            data = json.loads(raw)
            return AssistantResponse(**data)
        except Exception:
            return None


def generate_response(
    client: Mistral,
    transcript: str,
    class_level: str = "",
    subject: str = "auto",
) -> tuple[AssistantResponse | None, dict]:
    """Run the full LLM pipeline. Returns (response, timing)."""
    curriculum_matches = retrieve_curriculum(transcript)
    curriculum_context = format_curriculum_context(curriculum_matches)
    system_prompt = build_system_prompt(class_level, subject)

    base_text = (
        f'Teacher said: "{transcript}"\n\nUseful curriculum reference:\n{curriculum_context}'
        if curriculum_context
        else f'Teacher said: "{transcript}"'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": base_text},
    ]

    t0 = time.time()
    chat_response = client.chat.parse(
        model="mistral-large-2512",
        messages=messages,
        response_format={"type": "json_schema", "json_schema": {"name": "assistant_response", "schema": RESPONSE_SCHEMA}},
        max_tokens=2500,
        temperature=0.3,
        top_p=0.9,
        presence_penalty=0.1,
        frequency_penalty=0.1,
        safe_prompt=True,
    )
    llm_ms = int((time.time() - t0) * 1000)

    choice = chat_response.choices[0].message
    content = choice.content if isinstance(choice.content, str) else json.dumps(choice.content)
    parsed = parse_response(content)

    timing = {"llm_ms": llm_ms, "curriculum_hits": len(curriculum_matches)}
    return parsed, timing
