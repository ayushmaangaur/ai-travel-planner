from unittest.mock import MagicMock

import pytest

from app.travel_service import TravelService
from models.trip import TravelPlan


def test_travel_service_calls_root_agent():

    agent = MagicMock()

    expected_plan = TravelPlan(
        destination="Tokyo"
    )

    agent.plan_trip.return_value = expected_plan

    service = TravelService(agent)

    result = service.plan_trip(
        "Plan a trip to Tokyo"
    )

    assert result is expected_plan

    agent.plan_trip.assert_called_once_with(
        "Plan a trip to Tokyo"
    )


def test_travel_service_requires_agent():

    with pytest.raises(ValueError):
        TravelService(None)


def test_travel_service_rejects_non_string_message():

    agent = MagicMock()
    service = TravelService(agent)

    with pytest.raises(TypeError):
        service.plan_trip(123)


def test_travel_service_rejects_empty_message():

    agent = MagicMock()
    service = TravelService(agent)

    with pytest.raises(ValueError):
        service.plan_trip("   ")