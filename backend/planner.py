import json

from ai_provider import generate_ai_json

# ============================================================
# PLANNER AGENT
# ============================================================

PLANNER_SYSTEM_INSTRUCTION = """
You are the Planner Agent inside TripGenie AI.

Your job is to understand a user's travel request and convert it
into structured travel requirements for the other AI agents.

Extract:

- destination
- starting_location
- travelers
- duration
- travel_dates
- budget
- interests
- activities
- accommodation
- transportation
- food_preferences
- special_requirements

Rules:

1. Never invent information that is clearly not present.
2. If something is missing, use an empty string, empty list, or 0.
3. Infer obvious information only when it is safe and reasonable.
4. Keep the output valid JSON.
5. Do not add markdown.
6. Do not add explanations outside the JSON.

Return exactly this structure:

{
    "destination": "",
    "starting_location": "",
    "travelers": 0,
    "duration": "",
    "travel_dates": "",
    "budget": "",
    "interests": [],
    "activities": [],
    "accommodation": "",
    "transportation": "",
    "food_preferences": [],
    "special_requirements": []
}
"""

def plan_trip(user_request: str) -> dict:

    if not user_request or not user_request.strip():
        raise ValueError(
            "Travel request cannot be empty."
        )

    prompt = f"""
Analyze the following travel request.

USER REQUEST:
{user_request}

Extract the travel requirements and return ONLY
the required JSON structure.
"""

    try:

        print("[Planner Agent] Starting...")

        result = generate_ai_json(
            prompt=prompt,
            system_instruction=PLANNER_SYSTEM_INSTRUCTION,
        )

        print("[Planner Agent] Completed.")

        return result

    except json.JSONDecodeError as error:

        print(
            f"[Planner Agent] Invalid JSON returned: {error}"
        )

        raise RuntimeError(
            "Planner Agent received an invalid structured response."
        )

    except Exception as error:

        print(
            f"[Planner Agent] Failed: {error}"
        )

        raise RuntimeError(
            f"Planner Agent unavailable: {error}"
        )