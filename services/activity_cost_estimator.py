class ActivityCostEstimator:
    """
    Deterministic estimator for activity costs.

    Costs are estimated for the whole travel group rather than
    per person because BudgetEngine currently treats
    Activity.estimated_cost as a plan-level cost.
    """

    DEFAULT_COST = 500.0

    COST_RULES = {
        "arrival": 0.0,
        "check-in": 0.0,
        "departure": 0.0,
        "shopping": 0.0,

        "major attractions": 300.0,
        "sightseeing": 300.0,
        "attraction": 400.0,

        "beach": 300.0,
        "museum": 300.0,
        "fort": 200.0,
        "market": 200.0,
        "local experience": 500.0,
        "water sports": 1500.0,
        "restaurant": 0.0,
        "dinner": 0.0,
        "lunch": 0.0,
        "breakfast": 0.0,
    }

    def estimate(self, activity_name: str) -> float:
        """
        Return a deterministic estimated cost based on
        the activity name.
        """

        name = activity_name.lower()

        for keyword, cost in self.COST_RULES.items():
            if keyword in name:
                return cost

        return self.DEFAULT_COST