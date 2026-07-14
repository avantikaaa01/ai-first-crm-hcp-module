from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import hcp, interactions, chat

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM - HCP Module API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcp.router)
app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "hcp-crm-backend"}
