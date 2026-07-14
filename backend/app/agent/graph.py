"""
The LangGraph agent that powers the conversational Log Interaction chat.

Role of the agent:
Field reps talk in plain language ("Just met Dr. Mehta, she was happy with
DrugX results but wants more samples of DrugY, follow up in 2 weeks"). The
agent's job is to turn that into structured CRM data with zero manual form
entry, while staying auditable: it decides which tool(s) to call, calls them,
and narrates back what it did in plain language so the rep can confirm/correct
before anything is treated as final.

Graph shape:  START -> agent (LLM decides tool calls) -> tools (execute) -> agent -> ... -> END
This is the standard LangGraph ReAct loop: the agent node reasons + emits
tool calls; the tools node executes them and appends results; control
returns to the agent until it responds with plain text (no more tool calls).
"""
import datetime as dt
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from sqlalchemy.orm import Session
from .llm import get_llm
from .tools import build_tools

SYSTEM_PROMPT_TEMPLATE = """You are the HCP Interaction Agent inside a pharma field-rep CRM.
Your job is to help a field representative log, edit, and review their interactions
with Healthcare Professionals (HCPs) through natural conversation.

Today's date is {today}. When the rep mentions a relative date ("next week",
"in 2 weeks", "next month", "tomorrow"), calculate the actual calendar date
from today's date above before calling any tool - never guess or invent a date
from memory.

Rules:
- When the rep describes a visit/call, use the log_interaction tool to save it. Don't
  ask them to fill a form; extract what you can from their message. If you only have a
  doctor's name (no hcp_id in context), call search_hcp first to resolve it. If
  search_hcp returns more than one plausible match, ask the rep to confirm which one
  before logging.
- If they want to correct something already logged, use edit_interaction.
- If they ask "what happened last time" or similar, use get_hcp_history.
- If they ask to find/look up a doctor directly ("who do I have in Bengaluru cardiology"),
  use search_hcp and summarize the matches.
- If an interaction mentions specific product claims, you may proactively run
  check_compliance and mention the result.
- If the rep mentions a follow-up ("check back in 2 weeks"), use schedule_followup with
  the actual calculated ISO date (YYYY-MM-DD), based on today's date above.
- After any tool call, summarize the result back to the rep in one or two friendly,
  concise sentences. Never expose raw JSON to the rep.
- Be concise. You are a tool for a busy field rep between hospital visits, not a chatbot
  that likes to chat.
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_agent_graph(db: Session):
    tools = build_tools(db)
    llm = get_llm(temperature=0.2).bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        today_str = dt.datetime.now().strftime("%Y-%m-%d (%A)")
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(today=today_str)
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
