"""ChainFactor AI - FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.modules.ws.handler import websocket_invoice_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Migrations run via entrypoint.sh before uvicorn starts
    yield
    # Shutdown: close connections


app = FastAPI(
    title="ChainFactor AI",
    description="AI-powered invoice financing platform for Indian SMEs on Algorand",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.websocket("/ws/processing/{invoice_id}")
async def ws_invoice_processing(
    websocket: WebSocket,
    invoice_id: str,
    token: str | None = Query(default=None),
):
    """WebSocket endpoint for real-time invoice processing events.

    Connect to this endpoint after uploading an invoice.  Events are streamed
    as JSON objects until a ``pipeline_complete`` event is received.

    Query params:
        token: Optional Cognito JWT for future auth enforcement (currently logged only).

    Event types:
        step_complete     -- a pipeline step finished
        pipeline_complete -- the entire pipeline finished (decision + NFT)
        error             -- an unrecoverable error occurred
    """
    await websocket_invoice_handler(websocket, invoice_id, token=token)
