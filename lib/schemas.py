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
    mode: str  # "SIMPLIFY" or "QUIZ"
    audio_speech: str
    screen_data: Optional[ScreenData] = None
    quiz_data: Optional[QuizData] = None
