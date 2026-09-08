from models.trip import TravelPlan, DayPlan, Activity
from models.flight import FlightOption, FlightRecommendation
from models.hotel import HotelOption, HotelRecommendation
from services.plan_optimizer import PlanOptimizer


def test_optimizer_keeps_plan_within_budget():
    plan = TravelPlan(
        destination="Goa",
        itinerary=[
            DayPlan(
                day=1,
                title="Beach Day",
                summary="Relax at the beach",
                morning=[
                    Activity(
                        name="Beach",
                        description="Relax",
                        estimated_cost=100,
                    )
                ],
            )
        ],
        flights=FlightRecommendation(
            origin="Delhi",
            destination="Goa",
            options=[
                FlightOption(
                    airline="Air A",
                    price=12000,
                ),
                FlightOption(
                    airline="Air B",
                    price=7000,
                ),
            ],
        ),
        hotels=HotelRecommendation(
            destination="Goa",
            options=[
                HotelOption(
                    name="Luxury Hotel",
                    location="Goa",
                    rating=4.5,
                    price_per_night=5000,
                    currency="INR",
                    amenities=[],
                ),
                HotelOption(
                    name="Budget Hotel",
                    location="Goa",
                    rating=3.8,
                    price_per_night=2000,
                    currency="INR",
                    amenities=[],
                ),
            ],
        ),
    )

    optimizer = PlanOptimizer()

    result = optimizer.optimize(
        plan=plan,
        budget=15000,
        travelers=1,
        days=2,
    )

    assert result.budget_breakdown is not None
    assert result.budget_breakdown.within_budget

def test_optimizer_records_no_action_when_within_budget():
    plan = TravelPlan(
        destination="Goa",
        itinerary=[],
    )

    optimizer = PlanOptimizer()

    result = optimizer.optimize(
        plan=plan,
        budget=20000,
        travelers=1,
        days=2,
    )

    assert result.budget_breakdown is not None
    assert result.budget_breakdown.within_budget
    assert len(result.optimization_actions) == 1
    assert "No optimization required" in (
        result.optimization_actions[0]
    )


def test_optimizer_records_cheaper_flight():
    plan = TravelPlan(
        destination="Goa",
        itinerary=[],
        flights=FlightRecommendation(
            origin="Delhi",
            destination="Goa",
            options=[
                FlightOption(
                    airline="Expensive Air",
                    price=12000,
                ),
                FlightOption(
                    airline="Budget Air",
                    price=5000,
                ),
            ],
        ),
    )

    optimizer = PlanOptimizer()

    result = optimizer.optimize(
        plan=plan,
        budget=10000,
        travelers=1,
        days=2,
    )

    assert len(result.flights.options) == 1
    assert result.flights.options[0].airline == "Budget Air"

    assert any(
        "flight" in action.lower()
        for action in result.optimization_actions
    )


def test_optimizer_reports_remaining_overage():
    plan = TravelPlan(
        destination="Tokyo",
        itinerary=[],
    )

    optimizer = PlanOptimizer()

    result = optimizer.optimize(
        plan=plan,
        budget=1000,
        travelers=1,
        days=2,
    )

    assert result.budget_breakdown is not None
    assert not result.budget_breakdown.within_budget

    assert any(
        "over budget" in action.lower()
        for action in result.optimization_actions
    )