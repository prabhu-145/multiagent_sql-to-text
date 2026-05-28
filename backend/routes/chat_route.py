from fastapi import APIRouter
from pydantic import BaseModel
from agents.router_agent import route_query

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
def chat(request: ChatRequest):
    return route_query(request.query)
