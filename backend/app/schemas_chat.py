from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    reservation_id: int | None = None


class ToolTrace(BaseModel):
    tool: str
    detail: str = ""


class ChatResponse(BaseModel):
    message: str
    tool_traces: list[ToolTrace] = Field(default_factory=list)
