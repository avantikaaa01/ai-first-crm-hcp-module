import os
from langchain_groq import ChatGroq

GROQ_MODEL = os.getenv("GROQ_MODEL", "gemma2-9b-it")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile")


def get_llm(model: str | None = None, temperature: float = 0.2):
    """
    Returns a ChatGroq client.
    gemma2-9b-it is the primary model per the task spec (fast, cheap, good for
    structured extraction / summarization). llama-3.3-70b-versatile is kept as
    a fallback for turns that need stronger reasoning (e.g. ambiguous chat intent).
    """
    return ChatGroq(
        model=model or GROQ_MODEL,
        temperature=temperature,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def get_reasoning_llm(temperature: float = 0.2):
    """Heavier model for intent routing / multi-step reasoning in the agent."""
    return get_llm(model=GROQ_FALLBACK_MODEL, temperature=temperature)
