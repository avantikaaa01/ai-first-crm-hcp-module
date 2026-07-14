"""
The 5 LangGraph tools available to the HCP Interaction Agent.

1. log_interaction        - capture a new HCP interaction (summarize + extract entities via LLM)
2. edit_interaction        - modify a previously logged interaction
3. get_hcp_history          - pull an HCP's past interactions for context (grounds the LLM, avoids hallucination)
4. check_compliance         - flag off-label / regulatory-risk language before saving (pharma-specific guardrail)
5. schedule_followup        - set a follow-up reminder/task tied to an interaction

Each tool is a thin wrapper: it does deterministic DB work itself, and only
calls the LLM for the sub-task that genuinely needs language understanding
(summarizing free text, extracting topics/products, judging compliance risk).
This keeps the tools auditable -- a compliance reviewer can see exactly what
the DB write was, not just trust an LLM's full output.
"""
import datetime as dt
import json
from typing import List, Optional, Dict, Any
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import models
from .llm import get_llm

EXTRACTION_SYSTEM_PROMPT = """You are a clinical field-sales assistant. Given a field \
representative's raw notes about a visit with a Healthcare Professional (HCP), extract \
structured data. Respond ONLY with valid JSON, no markdown fences, no preamble, matching \
this schema:
{
  "summary": "<2-3 sentence neutral summary>",
  "interaction_type": "<Visit|Call|Email|Conference|Other>",
  "sentiment": "<Positive|Neutral|Negative>",
  "topics_discussed": ["<product or topic>", ...],
  "samples_distributed": [{"product": "<name>", "qty": <int>}],
  "follow_up_required": <true|false>,
  "follow_up_reason": "<short reason or empty string>"
}
"""

COMPLIANCE_SYSTEM_PROMPT = """You are a pharma compliance reviewer. Read the interaction \
summary and flag potential regulatory risks: off-label promotion, unsubstantiated efficacy \
claims, excessive/undocumented sample quantities, or inducement language. Respond ONLY with \
valid JSON: {"flag": <true|false>, "notes": "<short explanation, empty string if none>"}
"""


def _llm_json(system_prompt: str, user_content: str) -> dict:
    llm = get_llm(temperature=0.1)
    resp = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ])
    text = resp.content.strip()
    # defensive cleanup in case the model wraps in fences despite instructions
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def build_tools(db: Session) -> List[StructuredTool]:

    # ---------- 1. log_interaction ----------
    class LogInteractionInput(BaseModel):
        hcp_id: str = Field(description="ID of the HCP this interaction is with")
        raw_notes: str = Field(description="Free-text notes describing what happened during the visit/call")
        interaction_type: Optional[str] = Field(
            default=None, description="Visit, Call, Email, or Conference. Inferred from notes if omitted."
        )
        channel: str = Field(default="chat", description="'form' or 'chat' - how this was logged")

    def log_interaction(hcp_id: str, raw_notes: str, interaction_type: Optional[str] = None,
                         channel: str = "chat") -> str:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        extracted = _llm_json(EXTRACTION_SYSTEM_PROMPT, raw_notes)

        interaction = models.Interaction(
            hcp_id=hcp_id,
            interaction_type=interaction_type or extracted.get("interaction_type", "Visit"),
            channel=channel,
            date=dt.datetime.utcnow(),
            raw_text=raw_notes,
            summary=extracted.get("summary"),
            sentiment=extracted.get("sentiment"),
            topics_discussed=extracted.get("topics_discussed", []),
            samples_distributed=extracted.get("samples_distributed", []),
            follow_up_required=extracted.get("follow_up_required", False),
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "status": "logged",
            "interaction_id": interaction.id,
            "summary": interaction.summary,
            "sentiment": interaction.sentiment,
            "topics_discussed": interaction.topics_discussed,
            "follow_up_required": interaction.follow_up_required,
        })

    # ---------- 2. edit_interaction ----------
    class EditInteractionInput(BaseModel):
        interaction_id: str = Field(description="ID of the interaction to edit")
        changes: Dict[str, Any] = Field(
            description="Fields to update, e.g. {'notes': '...', 'topics_discussed': ['DrugX']}"
        )

    def edit_interaction(interaction_id: str, changes: Dict[str, Any]) -> str:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        # If raw notes changed, re-run extraction so summary/entities stay consistent
        if "notes" in changes and changes["notes"]:
            interaction.raw_text = changes["notes"]
            extracted = _llm_json(EXTRACTION_SYSTEM_PROMPT, changes["notes"])
            interaction.summary = extracted.get("summary", interaction.summary)
            interaction.sentiment = extracted.get("sentiment", interaction.sentiment)
            interaction.topics_discussed = extracted.get("topics_discussed", interaction.topics_discussed)

        for field in ["interaction_type", "topics_discussed", "samples_distributed",
                      "follow_up_required", "follow_up_date", "summary"]:
            if field in changes and changes[field] is not None:
                setattr(interaction, field, changes[field])

        interaction.updated_at = dt.datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "status": "updated",
            "interaction_id": interaction.id,
            "summary": interaction.summary,
            "topics_discussed": interaction.topics_discussed,
        })

    # ---------- 3. get_hcp_history ----------
    class GetHistoryInput(BaseModel):
        hcp_id: str = Field(description="ID of the HCP to fetch history for")
        limit: int = Field(default=5, description="Max number of past interactions to return")

    def get_hcp_history(hcp_id: str, limit: int = 5) -> str:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        rows = (
            db.query(models.Interaction)
            .filter(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.date.desc())
            .limit(limit)
            .all()
        )
        history = [{
            "date": r.date.isoformat() if r.date else None,
            "type": r.interaction_type,
            "summary": r.summary,
            "topics_discussed": r.topics_discussed,
        } for r in rows]

        return json.dumps({"hcp": hcp.name, "specialty": hcp.specialty, "history": history})

    # ---------- 4. search_hcp ----------
    class SearchHcpInput(BaseModel):
        query: str = Field(description="Free-text search: doctor name, specialty, hospital, or tier")

    def search_hcp(query: str) -> str:
        like = f"%{query}%"
        matches = (
            db.query(models.HCP)
            .filter(
                (models.HCP.name.ilike(like)) |
                (models.HCP.specialty.ilike(like)) |
                (models.HCP.hospital.ilike(like)) |
                (models.HCP.tier.ilike(like))
            )
            .limit(10)
            .all()
        )
        results = [{
            "id": h.id, "name": h.name, "specialty": h.specialty,
            "hospital": h.hospital, "tier": h.tier,
        } for h in matches]
        return json.dumps({"query": query, "results": results, "count": len(results)})

    # ---------- 5. check_compliance ----------
    class ComplianceInput(BaseModel):
        interaction_id: Optional[str] = Field(
            default=None, description="Existing interaction ID to check. If omitted, use summary_text."
        )
        summary_text: Optional[str] = Field(
            default=None, description="Raw text to check when no interaction_id is available yet"
        )

    def check_compliance(interaction_id: Optional[str] = None, summary_text: Optional[str] = None) -> str:
        text = summary_text
        interaction = None
        if interaction_id:
            interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
            if not interaction:
                return json.dumps({"error": f"No interaction found with id {interaction_id}"})
            text = interaction.summary or interaction.raw_text

        if not text:
            return json.dumps({"error": "No text provided to check"})

        result = _llm_json(COMPLIANCE_SYSTEM_PROMPT, text)
        flag = result.get("flag", False)
        notes = result.get("notes", "")

        if interaction:
            interaction.compliance_flag = flag
            interaction.compliance_notes = notes
            db.commit()

        return json.dumps({"compliance_flag": flag, "notes": notes})

    # ---------- 6. schedule_followup ----------
    class ScheduleFollowupInput(BaseModel):
        interaction_id: str = Field(description="Interaction this follow-up relates to")
        follow_up_date: str = Field(description="ISO date/datetime string for the follow-up, e.g. 2026-07-20")
        reason: Optional[str] = Field(default=None, description="Why the follow-up is needed")

    def schedule_followup(interaction_id: str, follow_up_date: str, reason: Optional[str] = None) -> str:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        try:
            parsed_date = dt.datetime.fromisoformat(follow_up_date)
        except ValueError:
            return json.dumps({"error": f"Could not parse date '{follow_up_date}', use ISO format YYYY-MM-DD"})

        interaction.follow_up_required = True
        interaction.follow_up_date = parsed_date
        if reason:
            interaction.compliance_notes = (interaction.compliance_notes or "") 
        db.commit()

        return json.dumps({
            "status": "scheduled",
            "interaction_id": interaction.id,
            "follow_up_date": parsed_date.isoformat(),
            "reason": reason,
        })

    return [
        StructuredTool.from_function(
            func=log_interaction, name="log_interaction",
            description="Log a new HCP interaction from free-text notes. Summarizes, extracts topics/samples via LLM, and saves to DB.",
            args_schema=LogInteractionInput,
        ),
        StructuredTool.from_function(
            func=edit_interaction, name="edit_interaction",
            description="Edit/correct a previously logged interaction (e.g. wrong product, add missed detail).",
            args_schema=EditInteractionInput,
        ),
        StructuredTool.from_function(
            func=get_hcp_history, name="get_hcp_history",
            description="Retrieve an HCP's recent interaction history, used to ground the agent's suggestions in real context.",
            args_schema=GetHistoryInput,
        ),
        StructuredTool.from_function(
            func=search_hcp, name="search_hcp",
            description="Search for an HCP by name, specialty, hospital, or tier. Use this when the rep names a doctor but you don't have their hcp_id yet.",
            args_schema=SearchHcpInput,
        ),
        StructuredTool.from_function(
            func=check_compliance, name="check_compliance",
            description="Check an interaction's text for regulatory/compliance risk (off-label claims, sample overages) before or after saving.",
            args_schema=ComplianceInput,
        ),
        StructuredTool.from_function(
            func=schedule_followup, name="schedule_followup",
            description="Schedule a follow-up task/reminder tied to a logged interaction.",
            args_schema=ScheduleFollowupInput,
        ),
    ]
