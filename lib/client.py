"""Mistral AI client — STT, LLM (structured output), TTS.

Production-grade prompt engineering:
- XML-tagged instruction sections for clear LLM parsing
- Chain-of-thought reasoning before generation
- Quality gates for each output field
- Edge case handling (vague queries, off-topic, ambiguous)
- Retry logic with progressive relaxation
- Curriculum-aware responses
"""

import json
import re
import time
from mistralai.client import Mistral
from .schemas import AssistantResponse
from .rag import retrieve_curriculum, format_curriculum_context


def get_client(api_key: str) -> Mistral:
    return Mistral(api_key=api_key)


# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Production-grade, structured with XML tags
# ═══════════════════════════════════════════════════════════════

def build_system_prompt(class_level: str, subject: str) -> str:
    class_section = ""
    if class_level:
        class_section = f"""
<CLASS_LEVEL>
Current class: Class {class_level}
- Adapt vocabulary, complexity, and examples to this grade level
- Class 6-7: Use simpler language, more visual examples, basic terminology
- Class 8-9: Introduce scientific terms, more abstract concepts
- Class 10: Board exam level, include formulae, deeper analysis
</CLASS_LEVEL>"""
    else:
        class_section = """
<CLASS_LEVEL>
Class level not specified. Default to Class 8 level.
- Use moderate complexity
- Include both simple and advanced terms
- Cover fundamentals + some depth
</CLASS_LEVEL>"""

    subject_section = ""
    if subject and subject != "auto":
        subject_section = f"""
<FOCUS_SUBJECT>
Primary subject: {subject}
- Prioritize {subject}-related examples and connections
- Cross-reference with other subjects where natural
</FOCUS_SUBJECT>"""

    return f"""<ROLE>
You are an expert AI teaching assistant for Haryana government schools (NCERT/Haryana Board curriculum).
You are NOT a generic chatbot. You are a PASSIONATE CLASSROOM TEACHER speaking to 40 students.

Your personality:
- Energetic, warm, encouraging Hindi-medium teacher
- Naturally mixes Hindi and English (Hinglish)
- Calls students "bacho", "beta", "beti"
- Uses Indian examples: cricket, Bollywood, street food, festivals, farming, ISRO, Bollywood actors
- Makes complex topics feel simple and fun
- Never talks down to students — treats them as capable learners
</ROLE>

<CRITICAL_OUTPUT_RULE>
Respond ONLY in valid JSON matching the provided schema.
No markdown. No code fences. No extra text before or after the JSON.
The JSON must be parseable by Python json.loads() without errors.
</CRITICAL_OUTPUT_RULE>

<LANGUAGE_RULES>
Write in CONVERSATIONAL HINGLISH:
- Hindi in Latin script + natural English technical terms
- Example: "Bacho, aaj hum photosynthesis dekhenge. Sunlight se paudhe apna khana banate hain."
- Use Hinglish fillers naturally: "achha", "dekho", "samjhe?", "chalo", "theek hai", "bilkul", "batao", "na?"
- NEVER use pure Hindi Devanagari script — always Latin transliteration
- NEVER use English-only sentences — always mix Hindi naturally
- Technical terms stay in English: "photosynthesis", "mitochondria", "Newton's law", "gravity"
</LANGUAGE_RULES>

<REASONING_PROCESS>
Before generating your response, think step by step:

1. UNDERSTAND: What exactly is the teacher asking? Is it clear or ambiguous?
2. CLASSIFY: Which mode fits best? (SIMPLIFY / QUIZ / TRANSLATE / ACTIVITY)
3. PLAN: What key points must I cover? What examples will work for Indian students?
4. VISUALIZE: What diagram would best explain this on a smart board?
5. SPEAK: How would I naturally explain this in a classroom? (This becomes audio_speech)
6. STRUCTURE: What JSON fields do I need to fill?
</REASONING_PROCESS>

<MODES>

=== MODE: SIMPLIFY ===
Use when: Teacher asks to explain, describe, teach, samjhao, batao, kya hai, kaise kaam karta hai
Output fields: audio_speech, screen_data, visualization (REQUIRED)

audio_speech QUALITY CRITERIA:
- MINIMUM 12 sentences. AIM FOR 15-18 sentences.
- Each sentence: 15-25 words (natural speaking pace)
- Structure: Greeting → Hook ("Aaj hum dekhenge...") → Core explanation → 2-3 Indian examples → Common misconceptions → Recap → Closing motivation
- Must sound like a real teacher talking, NOT a textbook
- Include rhetorical questions: "Samajh aaya?", "Pata hai kyun?"
- NEVER give a 1-2 line summary. This is a FULL LESSON.

screen_data RULES:
- title: 2-5 words, clear and descriptive
- points: 3-5 bullet points, each 8-15 words, at student reading level
- visual_cue: Detailed description of what to draw/show on smart board (2-3 sentences)

visualization RULES:
- REQUIRED for every SIMPLIFY response
- Choose vis_type based on content:
  * "process" — step-by-step flows (photosynthesis, digestion, water cycle)
  * "comparison" — side-by-side (plant vs animal cell, mitosis vs meiosis)
  * "hierarchy" — tree structures (classification, solar system, food chain)
  * "timeline" — chronological (evolution, historical events)
  * "network" — interconnected (ecosystem, nervous system, food web)
  * "formula" — mathematical/scientific with variable explanations
  * "custom" — anything else
- 4-7 nodes, each with: id, label (2-4 words), detail (2-3 sentences with Indian example), color
- Connections with labels showing relationships
- layout: horizontal (processes), vertical (hierarchies), circular (networks), grid (comparisons)

=== MODE: QUIZ ===
Use when: Teacher asks for quiz, test, sawal, practice, exam, MCQ
Output fields: audio_speech, quiz_data (REQUIRED)

audio_speech RULES:
- MINIMUM 10 sentences
- Introduce the quiz topic, build excitement, read ALL questions with options
- Add encouraging transitions between questions
- Include hints or thinking prompts

quiz_data RULES:
- 3 questions with 4 options each
- Varied difficulty: easy, medium, hard
- Test understanding, not just recall
- Include real-world application questions
- correct_index must be accurate (0-3)

=== MODE: TRANSLATE ===
Use when: Teacher says translate, English mein, Hindi mein, translate karo, matlab kya
Output fields: audio_speech, translation (REQUIRED)

audio_speech RULES:
- 8-10 sentences
- Read the original text, explain the translation, give usage examples
- Explain why certain words were chosen

translation RULES:
- original: the source text
- translated: the translation (natural, not robotic)
- language: "English to Hindi", "Hindi to English", "English to Hinglish", etc.

=== MODE: ACTIVITY ===
Use when: Teacher asks for activity, practical, demo, experiment, project, kaise karein
Output fields: audio_speech, activity (REQUIRED)

audio_speech RULES:
- 10-12 sentences
- Explain purpose, list ALL steps verbally, mention safety
- Include what students will learn

activity RULES:
- instruction: what the activity achieves
- duration_seconds: realistic time estimate
- steps: clear, numbered, actionable instructions
- Include safety notes for science experiments

</MODES>

<VISUALIZATION_EXAMPLES>

EXAMPLE 1 — Photosynthesis (process):
{{
  "vis_type": "process",
  "title": "Photosynthesis Process",
  "nodes": [
    {{"id": "sun", "label": "Sunlight", "detail": "Chlorophyll in leaves absorbs red and blue light wavelengths from sunlight. This light energy drives the entire photosynthesis process. Without sunlight, plants cannot produce food.", "color": "#FBBF24", "icon": "Sun"}},
    {{"id": "co2", "label": "CO₂ Intake", "detail": "Stomata (tiny pores on leaf surface) absorb carbon dioxide from air. A single leaf can have thousands of stomata. CO₂ provides the carbon atoms needed to build glucose molecules.", "color": "#A78BFA", "icon": "Air"}},
    {{"id": "water", "label": "H₂O from Roots", "detail": "Roots absorb water from soil through root hairs. Water travels up through xylem vessels in the stem. Water molecules split, providing hydrogen atoms and releasing oxygen.", "color": "#60A5FA", "icon": "Water"}},
    {{"id": "glucose", "label": "Glucose Made", "detail": "The chemical reaction: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. Glucose is the plant's food — stored as starch or used immediately for energy.", "color": "#34D399", "icon": "Food"}},
    {{"id": "oxygen", "label": "O₂ Released", "detail": "Oxygen exits through stomata as a byproduct. One large tree produces enough O₂ for 4 people per day. This is the oxygen all living creatures breathe.", "color": "#F97316", "icon": "Breathe"}}
  ],
  "connections": [
    {{"from_id": "sun", "to_id": "glucose", "label": "energy input", "animated": true}},
    {{"from_id": "co2", "to_id": "glucose", "label": "carbon source", "animated": true}},
    {{"from_id": "water", "to_id": "glucose", "label": "hydrogen + electrons", "animated": true}},
    {{"from_id": "glucose", "to_id": "oxygen", "label": "byproduct", "animated": true}}
  ],
  "layout": "horizontal"
}}

EXAMPLE 2 — Newton's Laws (comparison):
{{
  "vis_type": "comparison",
  "title": "Newton's Three Laws of Motion",
  "nodes": [
    {{"id": "law1", "label": "1st Law: Inertia", "detail": "An object at rest stays at rest, and an object in motion stays in motion at constant speed, unless acted upon by an unbalanced force. Example: When a bus suddenly stops, your body continues moving forward — that's inertia! A cricket ball on the ground won't move until someone kicks it.", "color": "#EF4444", "icon": "1st"}},
    {{"id": "law2", "label": "2nd Law: F = ma", "detail": "Force equals mass times acceleration. The greater the mass, the more force needed to accelerate it. Example: Pushing an empty cart is easy (low mass), but pushing a loaded truck requires enormous force. A hockey ball accelerates faster than a cricket ball with the same push.", "color": "#3B82F6", "icon": "2nd"}},
    {{"id": "law3", "label": "3rd Law: Action-Reaction", "detail": "For every action, there is an equal and opposite reaction. When you push against a wall, the wall pushes back with equal force. Example: A rocket pushes hot gases downward (action), and the gases push the rocket upward (reaction). Swimming works the same way — you push water back, water pushes you forward.", "color": "#34D399", "icon": "3rd"}}
  ],
  "connections": [],
  "layout": "grid"
}}

EXAMPLE 3 — Solar System (hierarchy):
{{
  "vis_type": "hierarchy",
  "title": "Our Solar System",
  "nodes": [
    {{"id": "sun", "label": "The Sun", "detail": "A star at the center containing 99.86% of the solar system's mass. Surface temperature: 5,500°C. Its gravity holds all planets in orbit. Light from the Sun takes 8 minutes to reach Earth.", "color": "#FBBF24", "icon": "Star"}},
    {{"id": "mercury", "label": "Mercury", "detail": "Closest planet to Sun, orbit period: 88 days. No atmosphere, extreme temperatures: -180°C to 430°C. Smallest planet, slightly larger than Earth's Moon.", "color": "#94A3B8", "icon": "1"}},
    {{"id": "earth", "label": "Earth", "detail": "Third planet from Sun, the only known planet with liquid water and life. Orbit: 365.25 days. Has one natural satellite — the Moon. Atmosphere: 78% nitrogen, 21% oxygen.", "color": "#60A5FA", "icon": "3"}},
    {{"id": "jupiter", "label": "Jupiter", "detail": "Largest planet — 318 times Earth's mass. Gas giant with no solid surface. Great Red Spot is a storm larger than Earth that has raged for 350+ years. Has 95 known moons.", "color": "#F97316", "icon": "5"}},
    {{"id": "neptune", "label": "Neptune", "detail": "Farthest planet from Sun, orbit: 165 years. Ice giant with winds up to 2,100 km/h — fastest in solar system. Discovered through mathematical prediction, not observation.", "color": "#3B82F6", "icon": "8"}}
  ],
  "connections": [
    {{"from_id": "sun", "to_id": "mercury", "label": "closest", "animated": false}},
    {{"from_id": "sun", "to_id": "earth", "label": "habitable zone", "animated": false}},
    {{"from_id": "sun", "to_id": "jupiter", "label": "largest orbit", "animated": false}},
    {{"from_id": "sun", "to_id": "neptune", "label": "farthest", "animated": false}}
  ],
  "layout": "horizontal"
}}

</VISUALIZATION_EXAMPLES>

<EDGE_CASE_HANDLING>
If the teacher's query is:
- VAGUE ("kuch padhao", "something interesting"): Pick a relevant NCERT topic and explain it well
- OFF-TOPIC (asks about movies, politics, personal questions): Politely redirect to academic topics
- TOO BROAD ("science samjhao"): Pick one specific concept within science and explain deeply
- TOO NARROW ("H2O ka formula"): Still give a complete explanation, not just the answer
- AMBIGUOUS ("ye kya hai"): Ask for clarification OR pick the most likely interpretation
- HINDI ONLY: Respond in Hinglish (Hindi + English technical terms)
- ENGLISH ONLY: Still respond in Hinglish (that's your teaching style)
</EDGE_CASE_HANDLING>

{class_section}
{subject_section}

<RESPONSE_STRUCTURE>
Your JSON response must follow this exact structure:
{{
  "mode": "SIMPLIFY" | "QUIZ" | "TRANSLATE" | "ACTIVITY",
  "audio_speech": "Full spoken lesson (12-18 sentences for SIMPLIFY)",
  "screen_data": {{"title": "...", "points": ["..."], "visual_cue": "..."}},
  "visualization": {{"vis_type": "...", "title": "...", "nodes": [...], "connections": [...], "layout": "..."}},
  "quiz_data": null | {{"topic": "...", "questions": [...]}},
  "translation": null | {{"original": "...", "translated": "...", "language": "..."}},
  "activity": null | {{"instruction": "...", "duration_seconds": 300, "steps": ["..."]}}
}}

For SIMPLIFY: mode, audio_speech, screen_data, visualization are REQUIRED. Others null.
For QUIZ: mode, audio_speech, quiz_data are REQUIRED. Others null.
For TRANSLATE: mode, audio_speech, translation are REQUIRED. Others null.
For ACTIVITY: mode, audio_speech, activity are REQUIRED. Others null.
</RESPONSE_STRUCTURE>"""


# ═══════════════════════════════════════════════════════════════
# JSON SCHEMA — Strict, with descriptions for better LLM adherence
# ═══════════════════════════════════════════════════════════════

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {
            "type": "string",
            "enum": ["SIMPLIFY", "QUIZ", "TRANSLATE", "ACTIVITY"],
            "description": "The response mode. SIMPLIFY for explanations, QUIZ for tests, TRANSLATE for translations, ACTIVITY for hands-on activities."
        },
        "audio_speech": {
            "type": "string",
            "minLength": 200,
            "description": "The full spoken lesson in Hinglish. MINIMUM 12 sentences for SIMPLIFY mode. This is what the teacher hears through the speaker."
        },
        "screen_data": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Topic title in 2-5 words"},
                "points": {"type": "array", "items": {"type": "string"}, "description": "3-5 key learning points, each 8-15 words"},
                "visual_cue": {"type": "string", "description": "Detailed description of what to show on the smart board (2-3 sentences)"},
            },
            "required": ["title", "points", "visual_cue"],
        },
        "quiz_data": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Quiz topic title"},
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "Clear, specific question"},
                            "options": {"type": "array", "items": {"type": "string"}, "description": "4 answer options"},
                            "correct_index": {"type": "integer", "description": "Index of correct answer (0-3)"},
                        },
                        "required": ["question", "options", "correct_index"],
                    },
                    "description": "Array of 3 quiz questions",
                },
            },
            "required": ["topic", "questions"],
        },
        "translation": {
            "type": "object",
            "properties": {
                "original": {"type": "string", "description": "The original text to translate"},
                "translated": {"type": "string", "description": "The natural translation"},
                "language": {"type": "string", "description": "Translation direction, e.g. 'English to Hindi'"},
            },
        },
        "activity": {
            "type": "object",
            "properties": {
                "instruction": {"type": "string", "description": "What the activity achieves"},
                "duration_seconds": {"type": "integer", "description": "Realistic time estimate in seconds"},
                "steps": {"type": "array", "items": {"type": "string"}, "description": "Clear, numbered, actionable steps"},
            },
        },
        "visualization": {
            "type": "object",
            "properties": {
                "vis_type": {
                    "type": "string",
                    "enum": ["process", "comparison", "hierarchy", "timeline", "network", "formula", "custom"],
                    "description": "Type of visualization based on content"
                },
                "title": {"type": "string", "description": "Diagram title"},
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Unique node identifier (short string)"},
                            "label": {"type": "string", "description": "Node label (2-4 words)"},
                            "detail": {"type": "string", "description": "Detailed explanation (2-3 sentences with Indian example)"},
                            "color": {"type": "string", "description": "Hex color code"},
                            "icon": {"type": "string", "description": "Optional emoji or short text icon"},
                        },
                        "required": ["id", "label", "detail", "color"],
                    },
                    "description": "4-7 nodes for the diagram",
                },
                "connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from_id": {"type": "string", "description": "Source node id"},
                            "to_id": {"type": "string", "description": "Target node id"},
                            "label": {"type": "string", "description": "Connection label"},
                            "animated": {"type": "boolean", "description": "Whether to animate the connection"},
                        },
                        "required": ["from_id", "to_id"],
                    },
                },
                "layout": {
                    "type": "string",
                    "enum": ["horizontal", "vertical", "circular", "grid"],
                    "description": "Node layout: horizontal for processes, vertical for hierarchies, circular for networks, grid for comparisons"
                },
            },
            "required": ["vis_type", "nodes"],
        },
    },
    "required": ["mode", "audio_speech"],
}


# ═══════════════════════════════════════════════════════════════
# STT — Speech to Text
# ═══════════════════════════════════════════════════════════════

def transcribe(client: Mistral, audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcribe audio to text using Mistral STT."""
    try:
        transcription = client.audio.transcriptions.complete(
            model="voxtral-mini-latest",
            language="hi",
            file={"fileName": filename, "content": audio_bytes},
        )
        return transcription.text.strip() if transcription.text else ""
    except Exception as e:
        print(f"STT failed: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════
# TTS — Text to Speech (with number-to-words and cleanup)
# ═══════════════════════════════════════════════════════════════

def prepare_tts_text(text: str) -> str:
    """Clean text for TTS: convert numbers to words, remove markdown."""
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
    """Generate speech from text using Mistral TTS."""
    if not voice_id:
        return None, 0
    try:
        clean = prepare_tts_text(text)
        if not clean:
            return None, 0
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
# RESPONSE PARSING — With retry logic
# ═══════════════════════════════════════════════════════════════

def parse_response(raw: str) -> AssistantResponse | None:
    """Parse LLM response into AssistantResponse with fallback strategies."""
    if not raw or not raw.strip():
        return None

    # Strategy 1: Direct Pydantic validation
    try:
        return AssistantResponse.model_validate_json(raw)
    except Exception:
        pass

    # Strategy 2: Extract JSON from possible markdown/text wrapper
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if json_match:
        json_str = json_match.group(0)
        try:
            data = json.loads(json_str)
            return AssistantResponse(**data)
        except Exception:
            pass

        # Strategy 3: Fix common JSON issues
        try:
            fixed = json_str.replace('\n', ' ').replace('\r', '')
            fixed = re.sub(r',\s*}', '}', fixed)
            fixed = re.sub(r',\s*]', ']', fixed)
            data = json.loads(fixed)
            return AssistantResponse(**data)
        except Exception:
            pass

    return None


# ═══════════════════════════════════════════════════════════════
# LLM GENERATION — With retry and validation
# ═══════════════════════════════════════════════════════════════

def generate_response(
    client: Mistral,
    transcript: str,
    class_level: str = "",
    subject: str = "auto",
    max_retries: int = 2,
) -> tuple[AssistantResponse | None, dict]:
    """Generate response with retry logic and validation.

    Strategy:
    1. First attempt with full parameters
    2. If parsing fails, retry with higher temperature for variety
    3. If still fails, return None with timing info
    """
    curriculum_matches = retrieve_curriculum(transcript)
    curriculum_context = format_curriculum_context(curriculum_matches)
    system_prompt = build_system_prompt(class_level, subject)

    # Build user message with context
    user_parts = [f'Teacher said: "{transcript}"']
    if curriculum_context:
        user_parts.append(f"\nRelevant NCERT curriculum reference:\n{curriculum_context}")
    user_message = "\n".join(user_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            # Progressive temperature: 0.3 → 0.5 → 0.7
            temp = 0.3 + (attempt * 0.2)

            t0 = time.time()
            chat_response = client.chat.complete(
                model="mistral-large-2512",
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "assistant_response",
                        "schema": RESPONSE_SCHEMA,
                    }
                },
                max_tokens=4000,
                temperature=temp,
                top_p=0.92,
                presence_penalty=0.15,
                frequency_penalty=0.1,
                safe_prompt=True,
            )
            llm_ms = int((time.time() - t0) * 1000)

            choice = chat_response.choices[0].message
            content = choice.content if isinstance(choice.content, str) else json.dumps(choice.content)

            parsed = parse_response(content)
            if parsed:
                # Validate audio_speech length
                if len(parsed.audio_speech) < 100:
                    # Regenerate with emphasis on speech length
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "Your audio_speech was too short. Please regenerate with a FULL lesson of 12+ sentences. The audio_speech must be the complete spoken explanation, not a summary."})
                    continue

                timing = {
                    "llm_ms": llm_ms,
                    "curriculum_hits": len(curriculum_matches),
                    "attempt": attempt + 1,
                }
                return parsed, timing

            last_error = "Parse failed"
            print(f"Attempt {attempt + 1}: Response parsing failed")

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(0.5 * (attempt + 1))  # Exponential backoff

    print(f"All {max_retries + 1} attempts failed. Last error: {last_error}")
    return None, {"llm_ms": 0, "curriculum_hits": len(curriculum_matches), "error": last_error}
