from ..services.portfolio_service import build_customer_portfolio
from ..services.scenario_minimum_service import simulate_minimum_payment_scenario
from ..services.scenario_optimized_service import simulate_optimized_plan
from ..services.scenario_consolidation_service import simulate_consolidation_scenario

from ..models.scenarios import (
    ScenarioComparisonResult,
    ScenarioSavings,
)


def compute_scenarios_overview(app, customer_id: str) -> ScenarioComparisonResult:
    """
    Calcula los tres escenarios para un cliente y devuelve
    el ahorro vs el escenario de pago mínimo.
    """
    data = app.state.data
    portfolio = build_customer_portfolio(app, customer_id)

    # 1) Escenario baseline: pago mínimo
    min_s = simulate_minimum_payment_scenario(portfolio)
    baseline_interest = min_s.total_interest_paid
    baseline_months = min_s.total_months

    scenarios_savings = []

    # Helper para armar cada item
    def _build_savings_item(scenario) -> ScenarioSavings:
        if scenario.scenario_type == "minimum_payment":
            interest_savings = 0.0
            months_saved = 0
        else:
            interest_savings = baseline_interest - scenario.total_interest_paid
            months_saved = baseline_months - scenario.total_months

        return ScenarioSavings(
            scenario_type=scenario.scenario_type,
            total_months=scenario.total_months,
            total_paid=scenario.total_paid,
            total_interest_paid=scenario.total_interest_paid,
            interest_savings_vs_minimum=interest_savings,
            months_saved_vs_minimum=months_saved,
        )

    # Agregamos mínimo (baseline)
    scenarios_savings.append(_build_savings_item(min_s))

    # 2) Escenario optimizado
    opt_s = simulate_optimized_plan(portfolio)
    scenarios_savings.append(_build_savings_item(opt_s))

    # 3) Escenario consolidación
    cons_s = simulate_consolidation_scenario(portfolio, data["bank_offers"])
    scenarios_savings.append(_build_savings_item(cons_s))

    # Resultado global
    return ScenarioComparisonResult(
        customer_id=customer_id,
        baseline_type="minimum_payment",
        baseline_total_months=baseline_months,
        baseline_total_interest_paid=baseline_interest,
        scenarios=scenarios_savings,
    )