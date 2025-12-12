import math
from typing import List

from ..models.portfolio import CustomerPortfolio
from ..models.scenarios import (
    ScenarioSummary,
    DebtAmortizationSummary,
)


def _monthly_rate(annual_rate_pct: float) -> float:
    """Convierte tasa anual en tasa mensual decimal."""
    return (annual_rate_pct / 100.0) / 12.0


def _simulate_card_minimum(
    balance: float,
    annual_rate_pct: float,
    min_payment_pct: float,
    max_months: int = 600,
) -> DebtAmortizationSummary:
    """
    Simula una tarjeta pagando siempre el mínimo.
    Regla simple:
      - pago_mínimo = balance * (min_payment_pct / 100)
      - interés_mes = balance * tasa_mensual
      - para evitar ciclos infinitos, si el pago mínimo
        no cubre el interés, forzamos pago = interés + 1
    """

    starting_balance = balance
    r = _monthly_rate(annual_rate_pct)

    total_paid = 0.0
    total_interest = 0.0
    months = 0

    while balance > 0.01 and months < max_months:
        interest = balance * r
        raw_min_payment = balance * (min_payment_pct / 100.0)
        payment = max(raw_min_payment, interest + 1.0, 10.0)  

        if payment > balance + interest:
            payment = balance + interest 

        principal_payment = payment - interest
        balance -= principal_payment

        total_paid += payment
        total_interest += interest
        months += 1

    return DebtAmortizationSummary(
        product_id="(card-aggregated)",
        product_type="card",
        starting_balance=starting_balance,
        total_paid=total_paid,
        total_interest_paid=total_interest,
        months_to_payoff=months,
    )


def _simulate_loan_standard(
    principal: float,
    annual_rate_pct: float,
    remaining_term_months: int,
) -> DebtAmortizationSummary:
    """
    Para el escenario 'pago mínimo' asumimos que el préstamo
    sigue su calendario normal de amortización (cuota fija).
    Usamos la fórmula clásica de anualidad.
    """

    starting_balance = principal
    r = _monthly_rate(annual_rate_pct)
    n = remaining_term_months

    if r == 0:
        monthly_payment = principal / n
    else:
        monthly_payment = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    total_paid = monthly_payment * n
    total_interest = total_paid - principal

    return DebtAmortizationSummary(
        product_id="(loan-aggregated)",
        product_type="loan",
        starting_balance=starting_balance,
        total_paid=total_paid,
        total_interest_paid=total_interest,
        months_to_payoff=n,
    )


def simulate_minimum_payment_scenario(
    portfolio: CustomerPortfolio,
) -> ScenarioSummary:
    """
    Escenario 1: El cliente paga:
      - Loans: según su plan actual de amortización.
      - Tarjetas: solo el pago mínimo.
    """

    debt_summaries: List[DebtAmortizationSummary] = []

    # --- Loans ---
    for loan in portfolio.loans:
        loan_summary = _simulate_loan_standard(
            principal=loan.principal,
            annual_rate_pct=loan.annual_rate_pct,
            remaining_term_months=loan.remaining_term_months,
        )
        loan_summary.product_id = loan.loan_id
        debt_summaries.append(loan_summary)

    # --- Cards ---
    for card in portfolio.cards:
        card_summary = _simulate_card_minimum(
            balance=card.balance,
            annual_rate_pct=card.annual_rate_pct,
            min_payment_pct=card.min_payment_pct,
        )
        card_summary.product_id = card.card_id
        debt_summaries.append(card_summary)

    # Agregamos la info total
    total_months = max(d.months_to_payoff for d in debt_summaries) if debt_summaries else 0
    total_paid = sum(d.total_paid for d in debt_summaries)
    total_interest = sum(d.total_interest_paid for d in debt_summaries)

    scenario = ScenarioSummary(
        customer_id=portfolio.customer_id,
        scenario_type="minimum_payment",
        total_months=total_months,
        total_paid=total_paid,
        total_interest_paid=total_interest,
        debts=debt_summaries,
    )

    return scenario