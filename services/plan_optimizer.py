from models.trip import TravelPlan
from services.budget_engine import BudgetEngine


class PlanOptimizer:
    """
    Deterministic optimization layer for travel plans.

    The optimizer does not use an LLM. It evaluates the generated
    travel plan against the user's budget and attempts to reduce
    costs using deterministic rules.
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

        # --------------------------------------------------------
        # INITIAL CALCULATION
        # --------------------------------------------------------

        breakdown = self.budget_engine.calculate(
            plan=plan,
            budget=budget,
            travelers=travelers,
            days=days,
        )

        # Already within budget
        if breakdown.within_budget:
            breakdown.optimization_actions = [
                "No optimization required. Plan is within budget."
            ]

            plan.budget_breakdown = breakdown
            plan.optimization_actions = (
                breakdown.optimization_actions
            )

            return plan

        actions.append(
            f"Initial estimated cost was ₹{breakdown.total:,.0f}, "
            f"which exceeds the ₹{budget:,.0f} budget."
        )

        # --------------------------------------------------------
        # STEP 1: CHEAPER FLIGHT
        # --------------------------------------------------------

        flight_changed = self._select_cheapest_flight(plan)

        if flight_changed:
            actions.append(
                "Selected the lowest-cost available flight option."
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

        # --------------------------------------------------------
        # STEP 2: CHEAPER HOTEL
        # --------------------------------------------------------

        hotel_changed = self._select_cheapest_hotel(plan)

        if hotel_changed:
            actions.append(
                "Selected the lowest-cost available hotel option."
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

        # --------------------------------------------------------
        # STEP 3: REMOVE EXPENSIVE ACTIVITIES
        # --------------------------------------------------------

        removed_activities = self._remove_expensive_activities(
            plan=plan,
            budget=budget,
            travelers=travelers,
            days=days,
        )

        for activity_name in removed_activities:
            actions.append(
                f"Removed high-cost activity: {activity_name}."
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

        # --------------------------------------------------------
        # COULD NOT FULLY OPTIMIZE
        # --------------------------------------------------------

        breakdown = self.budget_engine.calculate(
            plan=plan,
            budget=budget,
            travelers=travelers,
            days=days,
        )

        if breakdown.within_budget:
            actions.append(
                "Plan successfully brought within budget."
            )
        else:
            actions.append(
                f"Plan remains ₹{breakdown.exceeded_by:,.0f} "
                f"over budget after available optimizations."
            )

        return self._finalize(
            plan,
            breakdown,
            actions,
        )

    # ============================================================
    # FLIGHT OPTIMIZATION
    # ============================================================

    def _select_cheapest_flight(self, plan: TravelPlan) -> bool:

        if plan.flights is None:
            return False

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

        if not priced_options:
            return False

        cheapest = min(
            priced_options,
            key=lambda option: float(option.price),
        )

        # If already only has the cheapest option,
        # no actual optimization happened.
        if len(options) == 1 and options[0] is cheapest:
            return False

        plan.flights.options = [cheapest]

        return True

    # ============================================================
    # HOTEL OPTIMIZATION
    # ============================================================

    def _select_cheapest_hotel(self, plan: TravelPlan) -> bool:

        if plan.hotels is None:
            return False

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

        if not priced_options:
            return False

        cheapest = min(
            priced_options,
            key=lambda option: float(
                option.price_per_night
            ),
        )

        if len(options) == 1 and options[0] is cheapest:
            return False

        plan.hotels.options = [cheapest]

        return True

    # ============================================================
    # ACTIVITY OPTIMIZATION
    # ============================================================

    def _remove_expensive_activities(
        self,
        plan: TravelPlan,
        budget: float,
        travelers: int,
        days: int,
    ) -> list[str]:

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

            current_breakdown = self.budget_engine.calculate(
                plan=plan,
                budget=budget,
                travelers=travelers,
                days=days,
            )

            if current_breakdown.within_budget:
                break

            if self._remove_activity(plan, activity):
                removed.append(activity.name)

        return removed

    # ============================================================
    # REMOVE ACTIVITY
    # ============================================================

    def _remove_activity(
        self,
        plan: TravelPlan,
        target,
    ) -> bool:

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
        plan: TravelPlan,
        breakdown,
        actions: list[str],
    ) -> TravelPlan:

        breakdown.optimization_actions = actions

        plan.budget_breakdown = breakdown
        plan.optimization_actions = actions

        return plan