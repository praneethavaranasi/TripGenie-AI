import re

from ai_provider import generate_ai_json

# ============================================================
# ITINERARY AGENT
# ============================================================

ITINERARY_SYSTEM_INSTRUCTION = """
You are the Itinerary Agent inside TripGenie AI.

Your job is to transform the trip requirements, destination
research and budget analysis into a practical day-by-day
travel itinerary.

Return ONLY valid JSON.

Required structure:

{
    "destination": "",
    "trip_duration": "",
    "days": [
        {
            "day": 1,
            "title": "",
            "morning": [],
            "afternoon": [],
            "evening": [],
            "meals": [],
            "estimated_daily_cost": 0,
            "notes": ""
        }
    ],
    "total_estimated_cost": 0,
    "budget_status": "",
    "important_notes": []
}

Rules:

1. Create one itinerary entry for every day of the trip.

2. Respect the user's destination, duration, number of travelers,
   budget and interests.

3. Group attractions that are geographically sensible to visit
   together on the same day.

4. Avoid unrealistic schedules.

5. Include reasonable breaks and meal periods.

6. Use the research recommendations when appropriate.

7. Keep the itinerary consistent with the Budget Agent's
   estimated costs.

8. Do not claim that hotels, flights, restaurants, tickets or
   activities have actually been booked.

9. Estimated costs are approximate.

10. Do not invent confirmed live prices or availability.

11. Keep each day useful but not overloaded.

12. estimated_daily_cost should represent the approximate cost
    for that day's activities, food and relevant transportation
    for the entire group.

13. total_estimated_cost should represent the approximate total
    trip cost.

14. budget_status should reflect the Budget Agent's result.

15. Return JSON only.
"""


def extract_requested_days(trip_data: dict) -> int:
    duration = str(trip_data.get("duration", "")).strip().lower()
    if not duration:
        return 0

    match = re.search(r"(\d+)\s*(?:-|\s)?\s*day", duration)
    if match:
        return int(match.group(1))

    match = re.search(r"\d+", duration)
    if match:
        return int(match.group())

    return 0


def build_fallback_itinerary(
    trip_data: dict,
    research_data: dict | None = None,
    budget_data: dict | None = None,
) -> dict:

    destination = trip_data.get("destination", "Destination")
    duration = trip_data.get("duration", "")
    requested_days = extract_requested_days(trip_data)
    interests = trip_data.get("interests", [])
    research_data = research_data or {}
    budget_data = budget_data or {}

    if requested_days <= 0:
        requested_days = 1

    fallback_days = []
    recommended_places = research_data.get("recommended_places", [])
    place_names = [item.get("name", "") for item in recommended_places if isinstance(item, dict)]
    interest_text = ", ".join(interests) if isinstance(interests, list) else str(interests)

    for day_number in range(1, requested_days + 1):
        if day_number == 1:
            title = f"Arrival & {destination} highlights"
            morning = [f"Arrive in {destination} and settle in."]
            afternoon = [f"Explore {place_names[0] if place_names else 'the main beach area'}."]
            evening = ["Enjoy local food and a relaxed sunset walk."]
        elif day_number == requested_days:
            title = f"Leisure & departure"
            morning = ["Enjoy a slow morning with free time."]
            afternoon = ["Shop for souvenirs or revisit favorite spots."]
            evening = ["Prepare for departure with a final local meal."]
        else:
            title = f"{destination} day {day_number}"
            morning = [f"Start the day with a local breakfast and sightseeing in {destination}."]
            afternoon = [f"Focus on the day’s top interests: {interest_text or 'beaches and culture'}."]
            evening = ["Enjoy dinner and local nightlife or a beachside evening."]

        fallback_days.append(
            {
                "day": day_number,
                "title": title,
                "morning": morning,
                "afternoon": afternoon,
                "evening": evening,
                "meals": ["Breakfast", "Lunch", "Dinner"],
                "estimated_daily_cost": int((budget_data.get("estimated_cost", 0) or 0) / requested_days) if requested_days else 0,
                "notes": f"Planned for day {day_number} of the {duration or f'{requested_days}-day'} trip."
            }
        )

    estimated_cost = budget_data.get("estimated_cost", 0)
    if estimated_cost is None:
        estimated_cost = 0

    return {
        "destination": destination,
        "trip_duration": duration or f"{requested_days} days",
        "days": fallback_days,
        "total_estimated_cost": estimated_cost,
        "budget_status": budget_data.get("status", "WITHIN_BUDGET"),
        "important_notes": [
            "This itinerary was structured to cover the full trip duration.",
            "Costs are estimated and may vary by travel style.",
        ],
    }


def itinerary_trip(
    trip_data: dict,
    research_data: dict | None = None,
    budget_data: dict | None = None,
) -> dict:

    if not trip_data:
        raise ValueError(
            "Trip data cannot be empty."
        )

    research_data = research_data or {}
    budget_data = budget_data or {}

    requested_days = extract_requested_days(trip_data)

    prompt = f"""
Create a complete day-by-day travel itinerary using the
information below.

========================
TRIP REQUIREMENTS
========================

{trip_data}

========================
DESTINATION RESEARCH
========================

{research_data}

========================
BUDGET ANALYSIS
========================

{budget_data}

========================
TASK
========================

Create a practical itinerary.

Make sure:

- Every trip day is included.
- Activities match the user's interests.
- The schedule is geographically sensible.
- The budget is respected when possible.
- Food recommendations are incorporated.
- Transportation is practical.
- The itinerary is not overloaded.
- Estimated costs remain consistent with the Budget Agent.
- The itinerary must include exactly {requested_days} day entries.

Return ONLY the required JSON structure.
"""

    try:

        print("[Itinerary Agent] Starting...")

        result = generate_ai_json(
            prompt=prompt,
            system_instruction=ITINERARY_SYSTEM_INSTRUCTION,
        )

        print("[Itinerary Agent] Completed.")

        if not isinstance(result, dict):
            raise ValueError("Itinerary response is not a JSON object.")

        days = result.get("days", [])
        if not isinstance(days, list) or len(days) != requested_days:
            print(
                f"[Itinerary Agent] Invalid day count: "
                f"expected {requested_days}, got {len(days) if isinstance(days, list) else 'n/a'}. "
                "Applying deterministic fallback."
            )
            return build_fallback_itinerary(
                trip_data,
                research_data,
                budget_data,
            )

        normalized_days = []
        for index, day in enumerate(days, start=1):
            if not isinstance(day, dict):
                continue

            normalized_days.append(
                {
                    "day": day.get("day", index),
                    "title": day.get("title") or f"Day {index}",
                    "morning": day.get("morning", []),
                    "afternoon": day.get("afternoon", []),
                    "evening": day.get("evening", []),
                    "meals": day.get("meals", []),
                    "estimated_daily_cost": day.get("estimated_daily_cost", 0),
                    "notes": day.get("notes", ""),
                }
            )

        if len(normalized_days) != requested_days:
            print(
                "[Itinerary Agent] Normalized day count still mismatch. "
                "Applying deterministic fallback."
            )
            return build_fallback_itinerary(
                trip_data,
                research_data,
                budget_data,
            )

        result["destination"] = trip_data.get("destination", result.get("destination", "Destination"))
        result["trip_duration"] = trip_data.get("duration", result.get("trip_duration", ""))
        result["days"] = normalized_days
        result["total_estimated_cost"] = budget_data.get("estimated_cost", result.get("total_estimated_cost", 0))
        result["budget_status"] = budget_data.get("status", result.get("budget_status", "WITHIN_BUDGET"))
        result["important_notes"] = result.get("important_notes", [])

        return result

    except Exception as error:

        print(
            f"[Itinerary Agent] Failed: {error}"
        )

        return build_fallback_itinerary(
            trip_data,
            research_data,
            budget_data,
        )