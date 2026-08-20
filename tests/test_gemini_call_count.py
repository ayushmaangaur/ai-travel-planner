from agents.root_agent import RootTravelAgent


def test_complete_trip_uses_exactly_four_gemini_calls(monkeypatch):

    call_count = 0

    def fake_generate(self, prompt):

        nonlocal call_count
        call_count += 1

        print(f"\n===== FAKE GEMINI CALL #{call_count} =====")
        print(prompt[:500])
        print("=========================================\n")

        # Identify which type of prompt is being processed.
        if "Flight Agent" in prompt:
            return """
            {
                "origin": "Delhi",
                "destination": "Tokyo",
                "options": [
                    {
                        "airline": "Test Airline",
                        "flight_number": "TA123",
                        "departure_airport": "DEL",
                        "arrival_airport": "NRT",
                        "departure_time": "10:00",
                        "arrival_time": "20:00",
                        "duration": "10h",
                        "stops": 0,
                        "price": 20000,
                        "currency": "INR"
                    }
                ]
            }
            """

        if "Hotel Agent" in prompt:
            return """
            {
                "destination": "Tokyo",
                "options": [
                    {
                        "name": "Test Hotel",
                        "location": "Shinjuku",
                        "rating": 4.0,
                        "price_per_night": 4000,
                        "currency": "INR",
                        "amenities": ["Wi-Fi"]
                    }
                ]
            }
            """

        if "Weather Agent" in prompt:
            return """
            {
                "destination": "Tokyo",
                "forecast": [
                    {
                        "date": "Day 1",
                        "condition": "Sunny",
                        "temperature": "20°C",
                        "precipitation": "10%"
                    },
                    {
                        "date": "Day 2",
                        "condition": "Cloudy",
                        "temperature": "19°C",
                        "precipitation": "20%"
                    },
                    {
                        "date": "Day 3",
                        "condition": "Sunny",
                        "temperature": "21°C",
                        "precipitation": "10%"
                    }
                ]
            }
            """

        # Initial TravelRequest parsing.
        return """
        {
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 3,
            "budget": 60000,
            "travelers": 2,
            "preference": "cheap flights"
        }
        """

    monkeypatch.setattr(
        "services.llm_service.LLMService.generate",
        fake_generate
    )

    agent = RootTravelAgent()

    result = agent.plan_trip(
        "I am in Delhi and want to travel to Tokyo "
        "for 3 days with 2 people. "
        "My budget is 60000 rupees and I prefer cheap flights."
    )

    assert result.destination == "Tokyo"

    assert call_count == 3