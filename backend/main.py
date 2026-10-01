# ============================================================
# TRIPGENIE AI - FASTAPI BACKEND
# ============================================================

import json
import uuid
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from event_manager import event_manager
from supervisor_agent import TripSupervisor

# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="TripGenie AI",
    description="Agentic AI Travel Planning System",
    version="1.0.0"
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://trip-genie-ai-five.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# REQUEST MODEL
# ============================================================

class TravelRequest(BaseModel):

    request: str
    request_id: Optional[str] = None

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def home():

    return {
        "app": "TripGenie AI",
        "status": "online",
        "message": "Agentic AI Travel System is running!"
    }

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "agent_system": "ready"
    }

# ============================================================
# AGENT INFORMATION
# ============================================================

@app.get("/agents")
def agents():

    return {
        "agents": [
            "Supervisor Agent",
            "Planner Agent",
            "Research Agent",
            "Budget Agent",
            "Itinerary Agent",
            "Validation"
        ]
    }

# ============================================================
# PLAN TRIP
# ============================================================

@app.get("/plan-trip/events/{request_id}")
async def plan_trip_events(request_id: str):

    async def event_stream():
        async for event in event_manager.subscribe(request_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/plan-trip")
async def plan_trip(data: TravelRequest):

    request_id = data.request_id or str(uuid.uuid4())
    request = data.request.strip()

    if not request:

        return {
            "success": False,
            "request_id": request_id,
            "error": "Travel request cannot be empty."
        }

    try:

        supervisor = TripSupervisor()
        result = await supervisor.run(request, request_id)

        return {
            **result,
            "request_id": request_id,
        }

    except Exception as error:

        print(
            f"[FastAPI] Unexpected error: {error}"
        )

        return {
            "success": False,
            "request_id": request_id,
            "error": (
                "TripGenie encountered an unexpected error "
                "while creating your travel plan."
            ),
            "details": str(error)
        }