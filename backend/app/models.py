import uuid
import datetime as dt
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base


def gen_id():
    return str(uuid.uuid4())


class HCP(Base):
    """A Healthcare Professional (doctor) that a field rep engages with."""
    __tablename__ = "hcps"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    hospital = Column(String, nullable=True)
    tier = Column(String, nullable=True)  # e.g. "High Value", "Growth", "Maintain"
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """A single logged interaction between a field rep and an HCP."""
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=gen_id)
    hcp_id = Column(String, ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String, nullable=True)   # Visit, Call, Email, Conference
    channel = Column(String, nullable=True)             # form | chat
    date = Column(DateTime, default=dt.datetime.utcnow)

    raw_text = Column(Text, nullable=True)               # original rep notes / chat transcript
    summary = Column(Text, nullable=True)                # LLM-generated summary
    sentiment = Column(String, nullable=True)             # Positive / Neutral / Negative
    topics_discussed = Column(JSON, nullable=True)        # list of products/topics (entity extraction)
    samples_distributed = Column(JSON, nullable=True)     # list of {product, qty}
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    compliance_flag = Column(Boolean, default=False)      # flagged by compliance tool
    compliance_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
