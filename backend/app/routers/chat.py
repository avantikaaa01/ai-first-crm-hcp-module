from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from ..database import get_db
from .. import schemas
from ..agent.graph import build_agent_graph

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Naive in-memory session store keyed by session_id.
# Swap for Redis/DB-backed storage for multi-worker production deployments.
_SESSIONS: dict[str, list] = {}


@router.post("/", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatMessage, db: Session = Depends(get_db)):
    history = _SESSIONS.get(payload.session_id, [])

    user_content = payload.message
    if payload.hcp_id:
        # Give the agent the HCP id from UI context so it doesn't have to ask.
        user_content = f"[Context: hcp_id={payload.hcp_id}] {payload.message}"

    history.append(HumanMessage(content=user_content))

    graph = build_agent_graph(db)
    result = graph.invoke({"messages": history})

    _SESSIONS[payload.session_id] = result["messages"]

    final_message = result["messages"][-1]
    reply = final_message.content if isinstance(final_message, AIMessage) else str(final_message.content)

    tool_calls_log = [
        {"tool": m.name, "output": m.content}
        for m in result["messages"]
        if getattr(m, "type", None) == "tool"
    ]

    return schemas.ChatResponse(
        session_id=payload.session_id,
        reply=reply,
        tool_calls=tool_calls_log or None,
    )
