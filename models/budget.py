from dataclasses import dataclass


@dataclass
class BudgetBreakdown:
    budget: float

    flights: float = 0.0
    hotels: float = 0.0
    activities: float = 0.0
    food: float = 0.0
    transport: float = 0.0

    total: float = 0.0
    remaining: float = 0.0

    within_budget: bool = True
    budget_used_percentage: float = 0.0

    @property
    def exceeded_by(self) -> float:
        """Amount by which the trip exceeds the budget."""
        return max(0.0, self.total - self.budget)