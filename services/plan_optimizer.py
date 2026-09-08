from models.trip import TravelPlan
from models.budget import OptimizationAction
from services.budget_engine import BudgetEngine


class PlanOptimizer:

    """
    Deterministic optimization layer for travel plans.

    The optimizer evaluates a generated plan against the user's
    budget and applies deterministic cost-reduction strategies.
    """

    def __init__(self):
        self.budget_engine = BudgetEngine()

    def optimize(
        self,
        plan: TravelPlan,
        budget: float,
        travelers: int,
        days: int,
    ) -> TravelPlan:

        actions = []

        # ========================================================
        # INITIAL CALCULATION
        # ========================================================

        breakdown = self.budget_engine.calculate(
            plan=plan,
            budget=budget,
            travelers=travelers,
            days=days,
        )

        # ========================================================
        # ALREADY WITHIN BUDGET
        # ========================================================

        if breakdown.within_budget:

            breakdown.optimization_actions = []

            plan.budget_breakdown = breakdown
            plan.optimization_actions = []

            return plan

        actions.append(
            OptimizationAction(
                type="budget",
                action="initial_check",
                description=(
                    f"Initial estimated cost was "
                    f"₹{breakdown.total:,.0f}, exceeding the "
                    f"₹{budget:,.0f} budget."
                ),
                previous_cost=breakdown.total,
                new_cost=breakdown.total,
                savings=0.0,
            )
        )

        # ========================================================
        # STEP 1: CHEAPER FLIGHT
        # ========================================================

        flight_change = self._select_cheapest_flight(plan)

        if flight_change is not None:

            previous_cost, new_cost, description = flight_change

            actions.append(
                OptimizationAction(
                    type="flight",
                    action="select_cheaper",
                    description=description,
                    previous_cost=previous_cost,
                    new_cost=new_cost,
                    savings=max(
                        0.0,
                        previous_cost - new_cost,
                    ),
                )
            )

            breakdown = self.budget_engine.calculate(
                plan=plan,
                budget=budget,
                travelers=travelers,
                days=days,
            )

            if breakdown.within_budget:
                return self._finalize(
                    plan,
                    breakdown,
                    actions,
                )

        # ========================================================
        # STEP 2: CHEAPER HOTEL
        # ========================================================

        hotel_change = self._select_cheapest_hotel(plan)

        if hotel_change is not None:

            previous_cost, new_cost, description = hotel_change

            actions.append(
                OptimizationAction(
                    type="hotel",
                    action="select_cheaper",
                    description=description,
                    previous_cost=previous_cost,
                    new_cost=new_cost,
                    savings=max(
                        0.0,
                        previous_cost - new_cost,
                    ),
                )
            )

            breakdown = self.budget_engine.calculate(
                plan=plan,
                budget=budget,
                travelers=travelers,
                days=days,
            )

            if breakdown.within_budget:
                return self._finalize(
                    plan,
                    breakdown,
                    actions,
                )

        # ========================================================
        # STEP 3: REMOVE EXPENSIVE ACTIVITIES
        # ========================================================

        removed_activities = self._remove_expensive_activities(
            plan=plan,
            budget=budget,
            travelers=travelers,
            days=days,
        )

        for activity_name, activity_cost in removed_activities:

            actions.append(
                OptimizationAction(
                    type="activity",
                    action="remove",
                    description=(
                        f"Removed high-cost activity: "
                        f"{activity_name}"
                    ),
                    previous_cost=activity_cost,
                    new_cost=0.0,
                    savings=activity_cost,
                )
            )

            breakdown = self.budget_engine.calculate(
                plan=plan,
                budget=budget,
                travelers=travelers,
                days=days,
            )

            if breakdown.within_budget:
                return self._finalize(
                    plan,
                    breakdown,
                    actions,
                )

        # ========================================================
        # FINAL CALCULATION
        # ========================================================

        breakdown = self.budget_engine.calculate(
            plan=plan,
            budget=budget,
            travelers=travelers,
            days=days,
        )

        if breakdown.within_budget:
            actions.append(
                OptimizationAction(
                    type="budget",
                    action="within_budget",
                    description="Plan successfully brought within budget.",
                    previous_cost=breakdown.total,
                    new_cost=breakdown.total,
                    savings=0.0,
                )
            )
        else:
            actions.append(
                OptimizationAction(
                    type="budget",
                    action="over_budget",
                    description=(
                        f"Plan remains ₹{breakdown.exceeded_by:,.0f} "
                        f"over budget after available optimizations."
                    ),
                    previous_cost=breakdown.total,
                    new_cost=breakdown.total,
                    savings=0.0,
                )
            )

        return self._finalize(
            plan,
            breakdown,
            actions,
        )

    # ============================================================
    # FLIGHT OPTIMIZATION
    # ============================================================

    def _select_cheapest_flight(self, plan):

        if plan.flights is None:
            return None

        options = getattr(
            plan.flights,
            "options",
            [],
        )

        priced_options = [
            option
            for option in options
            if option.price is not None
        ]

        if len(priced_options) < 2:
            return None

        current = priced_options[0]

        cheapest = min(
            priced_options,
            key=lambda option: float(option.price),
        )

        if current is cheapest:
            return None

        previous_cost = float(current.price)
        new_cost = float(cheapest.price)

        plan.flights.options = [cheapest]

        description = (
            f"Selected {cheapest.airline}"
            f"{' ' + cheapest.flight_number if cheapest.flight_number else ''}"
        )

        return (
            previous_cost,
            new_cost,
            description,
        )

    # ============================================================
    # HOTEL OPTIMIZATION
    # ============================================================

    def _select_cheapest_hotel(self, plan):

        if plan.hotels is None:
            return None

        options = getattr(
            plan.hotels,
            "options",
            [],
        )

        priced_options = [
            option
            for option in options
            if option.price_per_night is not None
        ]

        if len(priced_options) < 2:
            return None

        current = priced_options[0]

        cheapest = min(
            priced_options,
            key=lambda option: float(
                option.price_per_night
            ),
        )

        if current is cheapest:
            return None

        previous_cost = float(
            current.price_per_night
        )

        new_cost = float(
            cheapest.price_per_night
        )

        plan.hotels.options = [cheapest]

        description = (
            f"Selected {cheapest.name}"
        )

        return (
            previous_cost,
            new_cost,
            description,
        )

    # ============================================================
    # ACTIVITY OPTIMIZATION
    # ============================================================

    def _remove_expensive_activities(
        self,
        plan,
        budget,
        travelers,
        days,
    ):

        activities = []

        for day in plan.itinerary:

            if not hasattr(day, "morning"):
                continue

            activities.extend(day.morning)
            activities.extend(day.afternoon)
            activities.extend(day.evening)

        activities = [
            activity
            for activity in activities
            if activity.estimated_cost is not None
            and float(activity.estimated_cost) > 0
        ]

        activities.sort(
            key=lambda activity: float(
                activity.estimated_cost
            ),
            reverse=True,
        )

        removed = []

        for activity in activities:

            current_breakdown = (
                self.budget_engine.calculate(
                    plan=plan,
                    budget=budget,
                    travelers=travelers,
                    days=days,
                )
            )

            if current_breakdown.within_budget:
                break

            cost = float(
                activity.estimated_cost
            )

            if self._remove_activity(
                plan,
                activity,
            ):
                removed.append(
                    (
                        activity.name,
                        cost,
                    )
                )

        return removed

    # ============================================================
    # REMOVE ACTIVITY
    # ============================================================

    def _remove_activity(
        self,
        plan,
        target,
    ):

        for day in plan.itinerary:

            if not hasattr(day, "morning"):
                continue

            if target in day.morning:
                day.morning.remove(target)
                return True

            if target in day.afternoon:
                day.afternoon.remove(target)
                return True

            if target in day.evening:
                day.evening.remove(target)
                return True

        return False

    # ============================================================
    # FINALIZE
    # ============================================================

    def _finalize(
        self,
        plan,
        breakdown,
        actions,
    ):

        breakdown.optimization_actions = actions

        plan.budget_breakdown = breakdown
        plan.optimization_actions = actions

        return plan