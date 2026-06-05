from fastapi import APIRouter
from pydantic import BaseModel
from agents.router_agent import route_query
from workflows.agent_graph import run_agent_graph

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
async def chat(request: dict):
    query = request.get("query")
    execution = run_graph_with_trace(query)
    return execution
