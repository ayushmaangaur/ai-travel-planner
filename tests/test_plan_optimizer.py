from models.trip import TravelPlan, DayPlan, Activity
from models.flight import FlightOption, FlightRecommendation
from models.hotel import HotelOption, HotelRecommendation
from services.plan_optimizer import PlanOptimizer
from models.budget import OptimizationAction


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
    assert result.optimization_actions == []


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

    flight_actions = [
        action
        for action in result.optimization_actions
        if action.type == "flight"
    ]

    assert len(flight_actions) == 1
    assert flight_actions[0].action == "select_cheaper"
    assert flight_actions[0].previous_cost == 12000
    assert flight_actions[0].new_cost == 5000
    assert flight_actions[0].savings == 7000


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
        "over budget" in action.description.lower()
        for action in result.optimization_actions
    )

def test_optimizer_records_structured_flight_action():
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

    assert len(result.optimization_actions) >= 1

    flight_actions = [
        action
        for action in result.optimization_actions
        if action.type == "flight"
    ]

    assert len(flight_actions) == 1

    action = flight_actions[0]

    assert isinstance(action, OptimizationAction)
    assert action.action == "select_cheaper"
    assert action.previous_cost == 12000
    assert action.new_cost == 5000
    assert action.savings == 7000

def test_optimizer_records_activity_removal():
    plan = TravelPlan(
        destination="Goa",
        itinerary=[
            DayPlan(
                day=1,
                title="Adventure",
                summary="Adventure day",
                morning=[
                    Activity(
                        name="Scuba Diving",
                        description="Scuba diving experience",
                        estimated_cost=5000,
                    ),
                    Activity(
                        name="Beach Walk",
                        description="Walk on the beach",
                        estimated_cost=500,
                    ),
                ],
            )
        ],
    )

    optimizer = PlanOptimizer()

    result = optimizer.optimize(
        plan=plan,
        budget=3000,
        travelers=1,
        days=2,
    )

    activity_actions = [
        action
        for action in result.optimization_actions
        if action.type == "activity"
    ]

    assert len(activity_actions) >= 1

    action = activity_actions[0]

    assert action.action == "remove"
    assert action.description.startswith(
        "Removed high-cost activity:"
    )
    assert action.previous_cost == 5000
    assert action.new_cost == 0
    assert action.savings == 5000

def test_no_optimization_actions_when_plan_is_within_budget():
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

    assert result.budget_breakdown.within_budget
    assert result.optimization_actions == []