from models.trip import (
    TravelPlan,
    DayPlan,
    Activity,
)

from services.budget_engine import BudgetEngine


def create_sample_plan():
    return TravelPlan(
        destination="Goa",
        itinerary=[
            DayPlan(
                day=1,
                title="North Goa",
                summary="Explore North Goa",
                morning=[
                    Activity(
                        name="Baga Beach",
                        description="Relax at Baga Beach",
                        estimated_cost=0,
                    )
                ],
                afternoon=[
                    Activity(
                        name="Fort Aguada",
                        description="Visit the historic fort",
                        estimated_cost=100,
                    )
                ],
                evening=[
                    Activity(
                        name="Night Market",
                        description="Explore local shopping",
                        estimated_cost=300,
                    )
                ],
            ),
            DayPlan(
                day=2,
                title="Old Goa",
                summary="Explore heritage sites",
                morning=[
                    Activity(
                        name="Basilica of Bom Jesus",
                        description="Visit the historic basilica",
                        estimated_cost=0,
                    )
                ],
                afternoon=[
                    Activity(
                        name="Museum",
                        description="Visit a local museum",
                        estimated_cost=200,
                    )
                ],
            ),
        ],
    )


def test_budget_calculation():

    engine = BudgetEngine()

    plan = create_sample_plan()

    result = engine.calculate(
        plan=plan,
        budget=30000,
        travelers=2,
        days=2,
    )

    assert result.budget == 30000

    assert result.activities == 600

    assert result.food == 2000

    assert result.transport == 1000

    assert result.total == 3600

    assert result.remaining == 26400

    assert result.within_budget is True


def test_budget_exceeded():

    engine = BudgetEngine()

    plan = create_sample_plan()

    result = engine.calculate(
        plan=plan,
        budget=3000,
        travelers=2,
        days=2,
    )

    assert result.within_budget is False

    assert result.exceeded_by == 600

    assert result.remaining == -600


def test_budget_percentage():

    engine = BudgetEngine()

    plan = create_sample_plan()

    result = engine.calculate(
        plan=plan,
        budget=7200,
        travelers=2,
        days=2,
    )

    assert result.total == 3600

    assert result.budget_used_percentage == 50


def test_zero_activity_cost():

    engine = BudgetEngine()

    plan = TravelPlan(
        destination="Goa",
        itinerary=[
            DayPlan(
                day=1,
                title="Beach Day",
                summary="Relax at the beach",
            )
        ],
    )

    result = engine.calculate(
        plan=plan,
        budget=10000,
        travelers=1,
        days=1,
    )

    assert result.activities == 0

    assert result.food == 500

    assert result.transport == 250

    assert result.total == 750


def test_negative_budget_is_rejected():

    engine = BudgetEngine()

    plan = create_sample_plan()

    try:
        engine.calculate(
            plan=plan,
            budget=-1000,
            travelers=2,
            days=2,
        )
        assert False
    except ValueError as exc:
        assert str(exc) == "Budget cannot be negative."


def test_invalid_travelers_are_rejected():

    engine = BudgetEngine()

    plan = create_sample_plan()

    try:
        engine.calculate(
            plan=plan,
            budget=30000,
            travelers=0,
            days=2,
        )
        assert False
    except ValueError as exc:
        assert str(exc) == "Travelers must be greater than zero."


def test_invalid_days_are_rejected():

    engine = BudgetEngine()

    plan = create_sample_plan()

    try:
        engine.calculate(
            plan=plan,
            budget=30000,
            travelers=2,
            days=0,
        )
        assert False
    except ValueError as exc:
        assert str(exc) == "Days must be greater than zero."