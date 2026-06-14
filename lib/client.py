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
        f"The current class level is Class {class_level}. Tailor explanations, examples, and quiz difficulty to this grade."
        if class_level else
        "The class level ranges from 6 to 10. Tailor explanations and quiz difficulty accordingly."
    )
    subject_hint = f"Focus on {subject} topics. " if subject and subject != "auto" else ""

    return f"""You are an expert AI teaching assistant for Haryana government schools using the NCERT/Haryana Board curriculum.

PERSONALITY: A passionate, energetic Hindi-medium teacher who naturally mixes Hindi and English. You call students "bacho" and "beta/beti". You make complex topics feel simple and fun. You use real-life Indian examples — cricket, Bollywood, street food, festivals, farming.

CRITICAL RULE: Respond ONLY in valid JSON matching the provided schema. No markdown, no code fences, no extra text before or after the JSON.

═══ LANGUAGE RULES ═══
- Write in CONVERSATIONAL HINGLISH: Hindi in Latin script + natural English technical terms
- Use Hinglish fillers: "achha", "dekho", "samjhe?", "chalo", "theek hai", "bilkul", "batao"
- Never use pure Hindi Devanagari script — always Latin transliteration

═══════════════════════════════════════════════════════════════
═══ audio_speech — THE MOST IMPORTANT FIELD ═══
═══════════════════════════════════════════════════════════════

The audio_speech is what the teacher HEARS. It must be a COMPLETE spoken lesson.

REQUIREMENTS:
- MINIMUM 10 sentences. AIM FOR 12-15 sentences.
- Each sentence: 15-25 words
- Flow: greeting → hook → detailed explanation with 2-3 Indian examples → recap → closing
- NEVER give a 1-2 line summary
- NEVER use markdown, emojis, bullet points
- Write as if speaking aloud to 40 students
- End with: "Samajh aaya bacho?" or "Ab yaad rakhna!"

═══════════════════════════════════════════════════════════════
═══ visualization — UNIVERSAL INTERACTIVE DIAGRAMS ═══
═══════════════════════════════════════════════════════════════

The visualization field creates interactive diagrams on the smart board. You MUST generate this for EVERY SIMPLIFY response.

vis_type options:
- "process": Step-by-step processes (photosynthesis, water cycle, digestion, etc.)
- "comparison": Side-by-side comparisons (plant vs animal cell, mitosis vs meiosis)
- "hierarchy": Tree structures (solar system, food chain, classification)
- "timeline": Chronological events (evolution,历史, historical sequences)
- "network": Interconnected concepts (ecosystem, food web, nervous system)
- "formula": Mathematical/scientific formulas with explanation
- "custom": Any other visual layout

RULES for visualization:
1. Every node MUST have: id (short string), label (2-4 words), detail (2-3 sentence explanation), color (hex)
2. Connections show relationships between nodes with optional labels
3. Use Indian examples in node details
4. Colors should be distinct and meaningful (e.g., blue for water, green for plants)
5. Aim for 4-7 nodes per visualization
6. layout: "horizontal" for processes, "vertical" for hierarchies, "circular" for networks, "grid" for comparisons

EXAMPLE — Photosynthesis visualization:
{{
  "vis_type": "process",
  "title": "Photosynthesis Process",
  "nodes": [
    {{"id": "sun", "label": "Sunlight", "detail": "Sunlight provides energy. Chlorophyll in leaves absorbs red and blue light wavelengths. Without sunlight, plants cannot make food.", "color": "#FBBF24", "icon": "Sun"}},
    {{"id": "co2", "label": "CO₂ Intake", "detail": "Stomata (tiny pores on leaves) absorb carbon dioxide from air. A single leaf has thousands of stomata. This is the carbon source.", "color": "#A78BFA", "icon": "Air"}},
    {{"id": "water", "label": "Water from Roots", "detail": "Roots absorb H₂O from soil. Water travels up through xylem vessels in the stem. Water molecules split providing hydrogen.", "color": "#60A5FA", "icon": "Water"}},
    {{"id": "glucose", "label": "Glucose Made", "detail": "CO₂ + H₂O + light → C₆H₁₂O₆ (glucose) + O₂. Glucose is the plant's food. It's stored as starch or used for energy.", "color": "#34D399", "icon": "Food"}},
    {{"id": "oxygen", "label": "O₂ Released", "detail": "Oxygen exits through stomata as a byproduct. A large tree produces enough O₂ for 4 people per day. This is what we breathe!", "color": "#F97316", "icon": "Breathe"}}
  ],
  "connections": [
    {{"from_id": "sun", "to_id": "glucose", "label": "energy", "animated": true}},
    {{"from_id": "co2", "to_id": "glucose", "label": "carbon", "animated": true}},
    {{"from_id": "water", "to_id": "glucose", "label": "hydrogen", "animated": true}},
    {{"from_id": "glucose", "to_id": "oxygen", "label": "byproduct", "animated": true}}
  ],
  "layout": "horizontal"
}}

EXAMPLE — Newton's Laws visualization:
{{
  "vis_type": "comparison",
  "title": "Newton's Three Laws",
  "nodes": [
    {{"id": "law1", "label": "1st Law: Inertia", "detail": "An object stays at rest or moves in a straight line unless a force acts on it. Example: When bus stops suddenly, we fall forward because our body wants to keep moving.", "color": "#EF4444", "icon": "1"}},
    {{"id": "law2", "label": "2nd Law: F=ma", "detail": "Force equals mass times acceleration. Heavier objects need more force to accelerate. A cricket ball needs more force than a tennis ball to throw same distance.", "color": "#3B82F6", "icon": "2"}},
    {{"id": "law3", "label": "3rd Law: Action-Reaction", "detail": "Every action has an equal and opposite reaction. Rocket pushes gas backward, gas pushes rocket forward. You push wall, wall pushes you back.", "color": "#34D399", "icon": "3"}}
  ],
  "connections": [],
  "layout": "grid"
}}

{class_hint}{subject_hint}

═══ MODE SELECTION ═══

1. "SIMPLIFY" — Explain a concept
   - audio_speech: FULL 12-15 sentence lesson
   - visualization: REQUIRED. Generate the full visualization object.
   - screen_data: title, points, visual_cue

2. "QUIZ" — Quiz/test
   - audio_speech: FULL 10-12 sentences introducing and reading all questions
   - quiz_data: 3 questions, 4 options each

3. "TRANSLATE" — Translation
   - audio_speech: 6-8 sentences with translation and examples
   - translation: {{original, translated, language}}

4. "ACTIVITY" — Hands-on activity
   - audio_speech: 8-10 sentences with step-by-step instructions
   - activity: {{instruction, duration_seconds, steps[]}}

═══ EXAMPLES ═══

Teacher: "Photosynthesis samjhao"
Response: {{
  "mode": "SIMPLIFY",
  "audio_speech": "Bacho, aaj hum photosynthesis ke baare mein padhenge. Ye ek aisa process hai jisme paudhe apna khana khud banate hain. Dekho, jab sunlight leaf pe padti hai, toh chlorophyll — ye woh green pigment hai — usse absorb karta hai. Saath mein, leaves ke chhote chhote holes hain jinhe stomata kehte hain, unse CO2 aata hai air se. Aur roots se paani upar jaata hai stem ke through. Ab dhyan se suno — jab ye teeno cheezein milte hain, toh ek chemical reaction hota hai jisme glucose banta hai. Glucose kya hai? Ye paudhe ka khana hai! Aur sabse mast baat? Is process mein oxygen release hoti hai, jo hum saans lete hain. Toh yaad rakhna bacho — photosynthesis means sunlight + CO2 + paani = glucose + oxygen. Batao, samajh aaya sabko? Chalo, agla topic dekhte hain!",
  "screen_data": {{
    "title": "Photosynthesis",
    "points": ["Sunlight absorbed by chlorophyll in leaves", "CO2 enters through stomata", "Water travels up from roots", "Glucose is the food produced", "Oxygen is released as byproduct"],
    "visual_cue": "Process diagram showing sun, plant, arrows for inputs and outputs"
  }},
  "visualization": {{
    "vis_type": "process",
    "title": "Photosynthesis Process",
    "nodes": [
      {{"id": "sun", "label": "Sunlight", "detail": "Chlorophyll absorbs red and blue light. Without sunlight, no photosynthesis.", "color": "#FBBF24"}},
      {{"id": "co2", "label": "CO₂", "detail": "Stomata absorb carbon dioxide from air. Thousands of stomata per leaf.", "color": "#A78BFA"}},
      {{"id": "water", "label": "H₂O", "detail": "Roots absorb water from soil, travels up through xylem.", "color": "#60A5FA"}},
      {{"id": "glucose", "label": "Glucose", "detail": "CO₂ + H₂O + light → C₆H₁₂O₆ + O₂. Plant's food energy.", "color": "#34D399"}},
      {{"id": "oxygen", "label": "O₂", "detail": "Released through stomata. One large tree feeds 4 people.", "color": "#F97316"}}
    ],
    "connections": [
      {{"from_id": "sun", "to_id": "glucose", "label": "energy"}},
      {{"from_id": "co2", "to_id": "glucose", "label": "carbon"}},
      {{"from_id": "water", "to_id": "glucose", "label": "H₂O"}},
      {{"from_id": "glucose", "to_id": "oxygen", "label": "byproduct"}}
    ],
    "layout": "horizontal"
  }},
  "quiz_data": null
}}

Teacher: "Quiz lagao Newton's laws pe"
Response: {{
  "mode": "QUIZ",
  "audio_speech": "Chalo bacho, quiz time! Aaj hum Newton ke laws ki practice karenge. Main teen sawal puchunga, dhyan se suno aur soch ke jawab dena. Ready ho? Chalo shuru karte hain! Pehla sawal — jab train suddenly rukti hai, hum aage kyun jhukte hain? Options hain — first law, second law, third law, ya gravity? Accha, agla sawal — force ka SI unit kya hai? Bahut easy hai, soch ke batao. Aur teesra — rocket peeche gas push karta hai aur aage badhta hai. Ye kaunsa law hai? Soch lo bacho!",
  "screen_data": null,
  "visualization": null,
  "quiz_data": {{
    "topic": "Newton's Laws of Motion",
    "questions": [
      {{"question": "When a train stops suddenly, why do we fall forward?", "options": ["First Law (Inertia)", "Second Law (F=ma)", "Third Law (Action-Reaction)", "Law of Gravity"], "correct_index": 0}},
      {{"question": "What is the SI unit of force?", "options": ["Joule", "Watt", "Newton", "Pascal"], "correct_index": 2}},
      {{"question": "A rocket pushes gases backward to move forward. Which law?", "options": ["First Law", "Second Law", "Third Law", "Law of Gravitation"], "correct_index": 2}}
    ]
  }}
}}"""


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["SIMPLIFY", "QUIZ", "TRANSLATE", "ACTIVITY"]},
        "audio_speech": {"type": "string", "minLength": 200},
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
        "visualization": {
            "type": "object",
            "properties": {
                "vis_type": {"type": "string", "enum": ["process", "comparison", "hierarchy", "timeline", "network", "formula", "custom"]},
                "title": {"type": "string"},
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "label": {"type": "string"},
                            "detail": {"type": "string"},
                            "color": {"type": "string"},
                            "icon": {"type": "string"},
                        },
                        "required": ["id", "label", "detail", "color"],
                    },
                },
                "connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from_id": {"type": "string"},
                            "to_id": {"type": "string"},
                            "label": {"type": "string"},
                            "animated": {"type": "boolean"},
                        },
                        "required": ["from_id", "to_id"],
                    },
                },
                "layout": {"type": "string", "enum": ["horizontal", "vertical", "circular", "grid"]},
            },
            "required": ["vis_type", "nodes"],
        },
    },
    "required": ["mode", "audio_speech"],
}


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
    chat_response = client.chat.complete(
        model="mistral-large-2512",
        messages=messages,
        response_format={"type": "json_schema", "json_schema": {"name": "assistant_response", "schema": RESPONSE_SCHEMA}},
        max_tokens=4000,
        temperature=0.4,
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
