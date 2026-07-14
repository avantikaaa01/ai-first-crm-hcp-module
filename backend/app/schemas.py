import datetime as dt
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None
    tier: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: str
    model_config = {"from_attributes": True}


class InteractionCreateForm(BaseModel):
    """Structured form submission."""
    hcp_id: str
    interaction_type: str
    date: Optional[dt.datetime] = None
    notes: str
    topics_discussed: Optional[List[str]] = None
    samples_distributed: Optional[List[Dict[str, Any]]] = None
    follow_up_required: Optional[bool] = False
    follow_up_date: Optional[dt.datetime] = None


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    notes: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    samples_distributed: Optional[List[Dict[str, Any]]] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[dt.datetime] = None
    summary: Optional[str] = None


class InteractionOut(BaseModel):
    id: str
    hcp_id: str
    interaction_type: Optional[str]
    channel: Optional[str]
    date: Optional[dt.datetime]
    raw_text: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    topics_discussed: Optional[List[str]]
    samples_distributed: Optional[List[Dict[str, Any]]]
    follow_up_required: Optional[bool]
    follow_up_date: Optional[dt.datetime]
    compliance_flag: Optional[bool]
    compliance_notes: Optional[str]

    model_config = {"from_attributes": True}


class ChatMessage(BaseModel):
    session_id: str
    message: str
    hcp_id: Optional[str] = None  # if already known from UI context


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    interaction: Optional[InteractionOut] = None
    awaiting_confirmation: bool = False
