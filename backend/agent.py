from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Create Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
You are TripGenie AI, an intelligent agentic travel-planning assistant.

Your goal is to help users create personalized and practical travel plans.

For every request:

1. Understand the destination.
2. Identify trip duration.
3. Identify number of travelers.
4. Identify the available budget.
5. Identify user interests and preferences.
6. Create a practical itinerary.
7. Organize activities logically based on location.
8. Estimate the major expenses.
9. Keep the estimated cost within the user's budget when possible.
10. Clearly state assumptions when information is missing.
11. If the user changes a requirement, adapt the existing plan.
12. Never claim that a hotel, flight, restaurant, or activity has
    actually been booked unless a real booking tool confirms it.

When generating a trip plan, use this structure:

DESTINATION
TRIP SUMMARY
BUDGET
DAY-BY-DAY ITINERARY
ACCOMMODATION
TRANSPORTATION
FOOD & EXPERIENCES
ESTIMATED COST
TRAVEL TIPS

Be concise but useful.
"""


def generate_trip_plan(user_request: str) -> str:
    """
    Generate a travel plan using Gemini.
    """

    if not user_request or not user_request.strip():
        return "Please provide your travel requirements."

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_request,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "temperature": 0.7,
            },
        )

        if response.text:
            return response.text

        return "The AI did not return a travel plan."

    except Exception as error:
        return f"AI Agent Error: {error}"


if __name__ == "__main__":

    print("=" * 60)
    print("\u2708\ufe0f  TRIPGENIE AI")
    print("Agent Test")
    print("=" * 60)

    request = """
    Plan a 5-day trip to Goa for 3 people.

    Budget: \u20b950,000

    Interests:
    - Beaches
    - Local food
    - Nightlife
    - Relaxing activities

    Create a practical day-by-day itinerary.
    """

    print("\n\U0001f916 Generating travel plan...\n")

    result = generate_trip_plan(request)

    print(result)