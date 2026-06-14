from pydantic import BaseModel, field_validator
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


class VisualizationNode(BaseModel):
    id: str
    label: str
    detail: str
    color: str = "#00d4aa"
    icon: str = ""


class VisualizationConnection(BaseModel):
    from_id: str
    to_id: str
    label: str = ""
    animated: bool = True


class Visualization(BaseModel):
    vis_type: str  # process | comparison | hierarchy | timeline | network | formula | custom
    title: str = ""
    nodes: list[VisualizationNode] = []
    connections: list[VisualizationConnection] = []
    layout: str = "horizontal"  # horizontal | vertical | circular | grid


class AssistantResponse(BaseModel):
    mode: str  # SIMPLIFY | QUIZ | TRANSLATE | ACTIVITY
    audio_speech: str
    screen_data: Optional[ScreenData] = None
    quiz_data: Optional[QuizData] = None
    translation: Optional[dict] = None
    activity: Optional[dict] = None
    visualization: Optional[Visualization] = None

    @field_validator("audio_speech")
    @classmethod
    def enforce_speech_length(cls, v: str) -> str:
        if len(v) < 100:
            raise ValueError(f"audio_speech too short ({len(v)} chars). Minimum 100 characters required.")
        return v
