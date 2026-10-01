import json

from ai_provider import generate_ai_json

# ============================================================
# RESEARCH AGENT
# ============================================================

RESEARCH_SYSTEM_INSTRUCTION = """
You are the Research Agent inside TripGenie AI.

Your job is to research and recommend useful travel options
based on the structured trip requirements provided by the
Planner Agent.

Return ONLY valid JSON.

Required structure:

{
    "destination_overview": "",
    "recommended_places": [],
    "recommended_activities": [],
    "food_recommendations": [],
    "transportation_options": [],
    "travel_tips": [],
    "research_notes": [],
    "requires_live_verification": []
}

RESEARCH RELIABILITY RULES:

1. Do not claim that prices, opening hours, availability,
   weather, bookings, transport schedules, or current events
   are live-verified unless an external source was actually used.
2. Clearly distinguish general destination knowledge from
   information requiring live verification.
3. Never invent URLs, citations, booking availability, ratings,
   current prices, or operating hours.
4. recommended_places should contain useful destination
   recommendations, but do not represent them as currently
   verified unless supported by external research.
5. requires_live_verification should list information that a
   traveler should verify before the trip.
6. research_notes should explain important limitations or
   assumptions in the research.
7. Keep recommendations relevant to the user's destination,
   duration, budget, interests, and preferences.

Return valid JSON only.
"""

_RESEARCH_SCALAR_FIELDS = (
    "destination",
    "starting_location",
    "travelers",
    "duration",
    "budget",
    "accommodation",
    "transportation",
)
_RESEARCH_LIST_FIELDS = (
    "interests",
    "activities",
    "food_preferences",
)


def _private_trip_data(trip_data: dict) -> dict:
    """Bound provider input and omit unknown or sensitive free-form fields."""
    safe_data = {}

    for field in _RESEARCH_SCALAR_FIELDS:
        value = trip_data.get(field)
        if isinstance(value, str):
            safe_data[field] = value[:120]
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            safe_data[field] = value

    for field in _RESEARCH_LIST_FIELDS:
        values = trip_data.get(field)
        if isinstance(values, list):
            safe_values = [
                value[:80]
                for value in values[:8]
                if isinstance(value, str)
            ]
            if safe_values:
                safe_data[field] = safe_values

    return safe_data


def research_trip(trip_data: dict) -> dict:

    if not trip_data:
        raise ValueError(
            "Trip data cannot be empty."
        )

    safe_trip_data = _private_trip_data(trip_data)

    prompt = f"""
Research the destination and travel options for the following
structured trip request.

TRIP REQUIREMENTS:

{json.dumps(safe_trip_data, ensure_ascii=False)}

Provide:

1. Destination overview
2. Recommended places
3. Recommended activities
4. Food recommendations
5. Transportation options
6. Useful travel tips
7. Research notes and assumptions
8. Information requiring live verification

Return ONLY the required JSON structure.
"""

    try:

        print("[Research Agent] Starting...")

        result = generate_ai_json(
            prompt=prompt,
            system_instruction=RESEARCH_SYSTEM_INSTRUCTION,
        )

        print("[Research Agent] Completed.")

        return result

    except Exception as error:

        print(
            f"[Research Agent] Failed: {error}"
        )

        raise RuntimeError(
            f"Research Agent unavailable: {error}"
        )