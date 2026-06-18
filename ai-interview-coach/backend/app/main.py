from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_utils import configure_logging
from app.routes.config_routes import router as config_router
from app.routes.debug_routes import router as debug_router
from app.routes.interview_routes import router as interview_router
from app.routes.session_routes import router as session_router
from app.routes.transcription_routes import router as transcription_router

configure_logging()

app = FastAPI(title="AI Interview Coach", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router)
app.include_router(debug_router)
app.include_router(interview_router)
app.include_router(transcription_router)
app.include_router(session_router)
