"""Main FastAPI backend entry point for CodePilot."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_chat import router as chat_router

app = FastAPI(
    title="CodePilot Backend API",
    description="Local AI Coding Assistant backend powered by Ollama",
    version="0.1.0",
)

# Allow CORS for local frontend development (React + Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "app": "CodePilot",
        "version": "0.1.0",
        "docs_url": "/docs",
    }
