from services.activity_cost_estimator import ActivityCostEstimator


def test_arrival_has_zero_cost():
    estimator = ActivityCostEstimator()

    assert estimator.estimate(
        "Arrival and check-in"
    ) == 0.0


def test_sightseeing_has_estimated_cost():
    estimator = ActivityCostEstimator()

    assert estimator.estimate(
        "Explore major attractions"
    ) == 300.0


def test_local_experience_has_estimated_cost():
    estimator = ActivityCostEstimator()

    assert estimator.estimate(
        "Local experience"
    ) == 500.0


def test_water_sports_are_more_expensive():
    estimator = ActivityCostEstimator()

    assert estimator.estimate(
        "Water sports"
    ) == 1500.0


def test_unknown_activity_uses_default_cost():
    estimator = ActivityCostEstimator()

    assert estimator.estimate(
        "Something completely unknown"
    ) == 500.0