"""Mistral AI client — STT, LLM (structured output), TTS."""

import json
import re
import time
from mistralai.client import Mistral
from .schemas import AssistantResponse
from .rag import retrieve_curriculum, format_curriculum_context


def get_client(api_key: str) -> Mistral:
    return Mistral(api_key=api_key)


def build_system_prompt(class_level: str, subject: str) -> str:
    class_hint = (
        f"The current class level is Class {class_level}. Tailor explanations and quiz difficulty to this grade."
        if class_level
        else "The class level ranges from 6 to 10. Tailor explanations and quiz difficulty accordingly."
    )
    subject_hint = (
        f"Focus on {subject} topics. " if subject and subject != "auto" else ""
    )

    return f"""You are an expert AI teaching assistant for Haryana government schools using the NCERT/Haryana Board curriculum. Respond exclusively in valid JSON matching the provided schema.

Rules:
1. Language: Fluid conversational Hinglish (Hindi in Latin script + natural English terms). Use words like "bacho", "dekhte hain", "samjhe?", "achha", "chalo". Make it sound like a passionate, energetic teacher connecting with secondary school students.
2. Audio speech: This is the FULL spoken explanation the teacher will hear. Write 6-10 sentences covering the ENTIRE concept thoroughly. Start with a hook ("Aaj hum dekhenge..."), explain each point in detail with examples, analogies, and real-world connections, and end with a summary ("Toh bacho, yaad rakhna..."). This should be the complete lesson — NOT a summary. The teacher relies on this audio as their primary learning channel.
3. Mode selection:
   - "SIMPLIFY": When the teacher asks to explain/samjhao a concept. Provide clear, accurate points tailored to the class level. Include a visual_cue describing what to display on the smart board.
   - "QUIZ": When the teacher asks for a quiz/test/sawal/practice. Generate 3-4 multiple choice questions with 4 options each.
4. Curriculum context (if provided) contains NCERT-aligned reference material. Use it to ensure accuracy, but explain in simple Hinglish.
5. Never use markdown, emojis, or special characters in audio_speech — it goes directly to TTS.
6. screen_data.title should be a short, catchy topic name (2-5 words).
7. screen_data.points should be 3-5 clear bullet points at a reading level appropriate for the class.
8. {class_hint}{subject_hint}"""


def transcribe(client: Mistral, audio_bytes: bytes, filename: str = "audio.webm") -> str:
    transcription = client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        language="hi",
        file={"fileName": filename, "content": audio_bytes},
    )
    return transcription.text.strip() if transcription.text else ""


def prepare_tts_text(text: str) -> str:
    def replace_num(d):
        num = int(d)
        if num == 0:
            return "zero"
        if num >= 1000:
            return d
        ones = [
            "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
        ]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        if num < 20:
            return ones[num]
        t, o = divmod(num, 10)
        return f"{tens[t]}-{ones[o]}" if o else tens[t]

    text = re.sub(r"\d+", replace_num, text)
    text = re.sub(r"[*_#`~\[\]()<>]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
    """Run the full LLM pipeline. Returns (response, timing_ms)."""
    curriculum_matches = retrieve_curriculum(transcript)
    curriculum_context = format_curriculum_context(curriculum_matches)

    system_prompt = build_system_prompt(class_level, subject)

    base_text = (
        f'Teacher said: "{transcript}"\n\nUseful curriculum reference:\n{curriculum_context}'
        if curriculum_context
        else f'Teacher said: "{transcript}"'
    )

    # Mistral chat.parse with JSON schema
    schema = {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["SIMPLIFY", "QUIZ"]},
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
        },
        "required": ["mode", "audio_speech", "screen_data", "quiz_data"],
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": base_text},
    ]

    t0 = time.time()
    chat_response = client.chat.parse(
        model="mistral-large-2512",
        messages=messages,
        response_format={"type": "json_schema", "json_schema": {"name": "assistant_response", "schema": schema}},
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


def synthesize_speech(client: Mistral, text: str, voice_id: str = "en_paul_neutral") -> tuple[str | None, int]:
    """TTS. Returns (base64_audio, tts_ms) or (None, 0) on failure."""
    if not voice_id:
        return None, 0
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
