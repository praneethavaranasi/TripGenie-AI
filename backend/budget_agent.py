from ai_provider import generate_ai_json

# ============================================================
# BUDGET AGENT
# ============================================================

BUDGET_SYSTEM_INSTRUCTION = """
You are the Budget Agent inside TripGenie AI.

Your job is to estimate the travel cost based on:

- Destination
- Number of travelers
- Trip duration
- User's stated budget
- Accommodation preferences
- Transportation
- Food preferences
- Activities
- Research recommendations

Return ONLY valid JSON.

Required structure:

{
    "currency": "INR",
    "budget_limit": 0,
    "estimated_cost": 0,
    "remaining_budget": 0,
    "status": "",
    "breakdown": {
        "accommodation": 0,
        "transportation": 0,
        "food": 0,
        "activities": 0,
        "miscellaneous": 0
    },
    "recommendations": []
}

Allowed status values:

WITHIN_BUDGET
OVER_BUDGET
BUDGET_NOT_SPECIFIED

Rules:

1. Use INR when the user is planning a trip in India unless
   another currency is explicitly requested.

2. If the user specifies a budget, try to keep the estimated
   plan within that budget.

3. If the budget is unrealistic, clearly indicate that through
   the status and recommendations.

4. Estimated costs are approximate and must not be presented
   as confirmed live prices.

5. Consider all travelers when calculating the total.

6. Consider the complete trip duration.

7. Accommodation, transportation, food, activities and
   miscellaneous costs should be included.

8. estimated_cost must represent the approximate TOTAL trip cost.

9. remaining_budget should be:

   budget_limit - estimated_cost

   when a budget is provided.

10. If no budget is provided, use:

   budget_limit = 0
   remaining_budget = 0
   status = "BUDGET_NOT_SPECIFIED"

11. Return JSON only.
"""

def budget_trip(
    trip_data: dict,
    research_data: dict | None = None,
) -> dict:

    if not trip_data:
        raise ValueError(
            "Trip data cannot be empty."
        )

    research_data = research_data or {}

    prompt = f"""
Analyze the following trip requirements and research information.

========================
TRIP REQUIREMENTS
========================

{trip_data}

========================
RESEARCH INFORMATION
========================

{research_data}

========================
TASK
========================

Estimate the complete trip cost.

Consider:

- Accommodation
- Transportation
- Food
- Activities
- Miscellaneous expenses
- Number of travelers
- Duration
- User's stated budget

Keep the estimate realistic and internally consistent.

Return ONLY the required JSON structure.
"""

    try:

        print("[Budget Agent] Starting...")

        result = generate_ai_json(
            prompt=prompt,
            system_instruction=BUDGET_SYSTEM_INSTRUCTION,
        )

        print("[Budget Agent] Completed.")

        return result

    except Exception as error:

        print(
            f"[Budget Agent] Failed: {error}"
        )

        raise RuntimeError(
            f"Budget Agent unavailable: {error}"
        )