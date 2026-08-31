from agents.root_agent import RootTravelAgent


# ============================================================
# COMPLETE REQUEST
# ============================================================

def test_complete_trip_does_not_need_gemini_for_request_parsing(
    monkeypatch,
):

    call_count = 0

    def fake_generate(self, prompt):

        nonlocal call_count

        call_count += 1

        if "Flight Agent" in prompt:
            return """
            {
                "origin": "Delhi",
                "destination": "Tokyo",
                "options": []
            }
            """

        if "Hotel Agent" in prompt:
            return """
            {
                "destination": "Tokyo",
                "options": []
            }
            """

        if "Weather Agent" in prompt:
            return """
            {
                "destination": "Tokyo",
                "forecast": []
            }
            """

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
        fake_generate,
    )

    agent = RootTravelAgent()

    result = agent.plan_trip(
        "I am in Delhi and want to travel to Tokyo "
        "for 3 days with 2 people. "
        "My budget is 60000 rupees."
    )

    assert result.destination == "Tokyo"

    # The three specialized agents may use Gemini,
    # but the initial request itself should be parsed locally.
    assert call_count == 3


# ============================================================
# FOLLOW-UP SHOULD NOT CALL GEMINI
# ============================================================

def test_follow_up_does_not_call_gemini(monkeypatch):

    call_count = 0

    def fake_generate(self, prompt):

        nonlocal call_count
        call_count += 1

        if "Flight Agent" in prompt:
            return """
            {
                "origin": "Delhi",
                "destination": "Tokyo",
                "options": []
            }
            """

        if "Hotel Agent" in prompt:
            return """
            {
                "destination": "Tokyo",
                "options": []
            }
            """

        if "Weather Agent" in prompt:
            return """
            {
                "destination": "Tokyo",
                "forecast": []
            }
            """

        raise AssertionError(
            "Gemini should not be used for complete local extraction"
        )

    monkeypatch.setattr(
        "services.llm_service.LLMService.generate",
        fake_generate,
    )

    agent = RootTravelAgent()

    # First message.
    result = agent.plan_trip(
        "I am in Delhi and want to travel to Tokyo "
        "for 7 days with 2 people. "
        "My budget is 50000 rupees."
    )

    assert result.destination == "Tokyo"

    calls_after_first_request = call_count

    # Follow-up.
    result = agent.plan_trip(
        "Actually make it 5 days."
    )

    # Follow-up parsing should happen locally.
    assert agent.session.request.days == 5

    assert call_count == calls_after_first_request