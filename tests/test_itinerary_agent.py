import json

from agents.itinerary_agent import ItineraryAgent
from models.trip import TravelRequest, DayPlan


def test_itinerary_agent_returns_correct_number_of_days(
    monkeypatch
):

    agent = ItineraryAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=3,
        budget=50000,
        travelers=2,
        preference="cheap"
    )

    fake_response = json.dumps([
        {
            "day": 1,
            "title": "Arrival in Tokyo",
            "summary": "Settle in and explore Shibuya.",
            "morning": [
                {
                    "name": "Shibuya Crossing",
                    "description": "Explore the famous crossing.",
                    "location": "Shibuya",
                    "duration": "1 hour",
                    "estimated_cost": 0
                }
            ],
            "afternoon": [],
            "evening": [],
            "meals": ["Try ramen"],
            "travel_tips": ["Use the metro"],
            "weather_note": "Check weather before walking."
        },
        {
            "day": 2,
            "title": "Traditional Tokyo",
            "summary": "Explore Asakusa and nearby attractions.",
            "morning": [],
            "afternoon": [],
            "evening": [],
            "meals": [],
            "travel_tips": [],
            "weather_note": None
        },
        {
            "day": 3,
            "title": "Tokyo Finale",
            "summary": "Shopping and sightseeing.",
            "morning": [],
            "afternoon": [],
            "evening": [],
            "meals": [],
            "travel_tips": [],
            "weather_note": None
        }
    ])

    monkeypatch.setattr(
        agent.llm,
        "generate",
        lambda prompt: fake_response
    )

    result = agent.generate(
        request,
        None,
        None,
        None
    )

    assert len(result) == 3
    assert all(
        isinstance(day, DayPlan)
        for day in result
    )

def test_itinerary_agent_uses_destination(monkeypatch):

    agent = ItineraryAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=1,
        budget=50000,
        travelers=2,
    )

    captured_prompt = {}

    def fake_generate(prompt):

        captured_prompt["value"] = prompt

        return json.dumps([
            {
                "day": 1,
                "title": "Tokyo",
                "summary": "Explore Tokyo.",
                "morning": [],
                "afternoon": [],
                "evening": [],
                "meals": [],
                "travel_tips": [],
                "weather_note": None
            }
        ])

    monkeypatch.setattr(
        agent.llm,
        "generate",
        fake_generate
    )

    agent.generate(
        request,
        None,
        None,
        None
    )

    assert "Tokyo" in captured_prompt["value"]