from pydantic import BaseModel
from typing import Optional


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int


class ScreenData(BaseModel):
    title: str
    points: list[str]
    visual_cue: str


class QuizData(BaseModel):
    topic: str
    questions: list[QuizQuestion]


class AssistantResponse(BaseModel):
    mode: str  # SIMPLIFY | QUIZ | TRANSLATE | ACTIVITY
    audio_speech: str
    screen_data: Optional[ScreenData] = None
    quiz_data: Optional[QuizData] = None
    translation: Optional[dict] = None  # {"original": str, "translated": str, "language": str}
    activity: Optional[dict] = None  # {"instruction": str, "duration_seconds": int, "steps": list[str]}
