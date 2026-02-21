from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    url: str
    memory_used: bool
    history: list[dict]