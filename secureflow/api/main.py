"""
SecureFlow — FastAPI Application
Main entry point for the SecureFlow API server.

Mounts all route modules:
  - /health            → readiness probe
  - /webhook/gitlab    → GitLab webhook receiver
  - /api/findings      → security findings CRUD
  - /api/approvals     → HITL approval queue

In production, also serves the React dashboard from /assets.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from secureflow.api.health import router as health_router
from secureflow.api.webhook import router as webhook_router
from secureflow.api.findings import router as findings_router
from secureflow.api.approvals import router as approvals_router


# Configure logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Create FastAPI app

app = FastAPI(
    title="SecureFlow API",
    description=(
        "Autonomous software supply chain security agent. "
        "Powered by Google ADK + Gemini + GitLab MCP."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS middleware (allows dashboard to call API)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # React dev server
        "http://localhost:8000",   # Same-origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount routers

# Health check at root level
app.include_router(health_router)

# Webhook at root level (/webhook/gitlab)
app.include_router(webhook_router)

# API endpoints under /api prefix
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")
api_router.include_router(findings_router)
api_router.include_router(approvals_router)
app.include_router(api_router)



# Root endpoint

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "SecureFlow",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }



# Startup event

@app.on_event("startup")
async def startup_event():
    logger.info("SecureFlow API starting up...")
    logger.info("BigQuery: using in-memory store (development mode)")
    logger.info("Endpoints: /health, /webhook/gitlab, /api/findings, /api/approvals")
    logger.info("Docs: http://localhost:8000/docs")
