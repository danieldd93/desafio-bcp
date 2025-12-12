from typing import List, Literal
from pydantic import BaseModel


ScenarioType = Literal["minimum_payment", "optimized_plan", "consolidation"]


class DebtAmortizationSummary(BaseModel):
    product_id: str
    product_type: Literal["loan", "card"]
    starting_balance: float
    total_paid: float
    total_interest_paid: float
    months_to_payoff: int


class ScenarioSummary(BaseModel):
    customer_id: str
    scenario_type: ScenarioType
    total_months: int
    total_paid: float
    total_interest_paid: float
    debts: List[DebtAmortizationSummary]

class ScenarioSavings(BaseModel):
    scenario_type: ScenarioType
    total_months: int
    total_paid: float
    total_interest_paid: float
    interest_savings_vs_minimum: float
    months_saved_vs_minimum: int


class ScenarioComparisonResult(BaseModel):
    customer_id: str
    baseline_type: ScenarioType
    baseline_total_months: int
    baseline_total_interest_paid: float
    scenarios: List[ScenarioSavings]