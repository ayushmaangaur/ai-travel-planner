from dataclasses import dataclass, field


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
    optimization_actions: list[str] = field(default_factory=list)

    @property
    def exceeded_by(self) -> float:
        return max(0.0, self.total - self.budget)