from typing import List, Optional

from ..models.portfolio import CustomerPortfolio, BankOffer
from ..models.scenarios import ScenarioSummary, DebtAmortizationSummary


def _monthly_rate(annual_rate_pct: float) -> float:
    return (annual_rate_pct / 100.0) / 12.0


def _loan_monthly_payment(principal: float, annual_rate_pct: float, term_months: int) -> float:
    """
    Cuota fija estándar de un préstamo (anualidad).
    """
    r = _monthly_rate(annual_rate_pct)
    n = term_months

    if n <= 0:
        return principal

    if r == 0:
        return principal / n

    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def _parse_offers(offers_raw) -> List[BankOffer]:
    """
    Convierte la lista/dict cruda de JSON en modelos BankOffer.
    """
    offers: List[BankOffer] = []
    for o in offers_raw:
        offers.append(BankOffer(**o))
    return offers


def simulate_consolidation_scenario(
    portfolio: CustomerPortfolio,
    offers_raw,
) -> ScenarioSummary:
    """
    Escenario 3: Consolidación de deudas.

    Lógica:
      - Para cada oferta:
          * Calculamos el saldo total elegible (loans y cards permitidos).
          * Verificamos condiciones (score, mora, tope de saldo).
          * Calculamos la cuota con la tasa/plazo de la oferta.
          * Validamos que la cuota mensual <= available_cashflow.
      - Elegimos la oferta que resulte en MENOS intereses totales
        (y en caso de empate, menor plazo).
      - Devolvemos un ScenarioSummary con un solo "préstamo consolidado".
    """

    offers = _parse_offers(offers_raw)
    available_cf = portfolio.cashflow.available_cashflow

    if available_cf <= 0 or not offers:
        return ScenarioSummary(
            customer_id=portfolio.customer_id,
            scenario_type="consolidation",
            total_months=0,
            total_paid=0.0,
            total_interest_paid=0.0,
            debts=[],
        )

    best_summary: Optional[ScenarioSummary] = None

    for offer in offers:
        # 1) Determinar qué deudas son elegibles para esta oferta
        eligible_balance = 0.0
        max_days_past_due = 0

        # Loans
        for loan in portfolio.loans:
            if loan.product_type in offer.product_types_eligible:
                eligible_balance += loan.principal
                max_days_past_due = max(max_days_past_due, loan.days_past_due)

        # Cards
        for card in portfolio.cards:
            if "card" in offer.product_types_eligible:
                eligible_balance += card.balance
                max_days_past_due = max(max_days_past_due, card.days_past_due)

        # Si no hay nada que consolidar con esta oferta, seguimos
        if eligible_balance <= 0:
            continue

        # 2) Respetar máximo saldo consolidado
        if eligible_balance > offer.max_consolidated_balance:
            continue

        # 3) Verificar condiciones del texto (simplificadas)
        cond = offer.conditions.lower()

        # Condición de score
        if "score > 650" in cond:
            if portfolio.credit_score is None or portfolio.credit_score <= 650:
                continue

        # Condición de mora
        if "no mora >30" in cond or "no mora > 30" in cond or "sin mora activa" in cond:
            if max_days_past_due > 30:
                continue

        # 4) Calcular la cuota del nuevo crédito consolidado
        n = offer.max_term_months
        monthly_payment = _loan_monthly_payment(
            principal=eligible_balance,
            annual_rate_pct=offer.new_rate_pct,
            term_months=n,
        )

        # Si la cuota no cabe en el flujo de caja, descartamos la oferta
        if monthly_payment > available_cf:
            continue

        total_paid = monthly_payment * n
        total_interest = total_paid - eligible_balance

        # 5) Crear el resumen para esta oferta
        debt_summary = DebtAmortizationSummary(
            product_id=offer.offer_id,
            product_type="loan",
            starting_balance=eligible_balance,
            total_paid=total_paid,
            total_interest_paid=total_interest,
            months_to_payoff=n,
        )

        scenario_summary = ScenarioSummary(
            customer_id=portfolio.customer_id,
            scenario_type="consolidation",
            total_months=n,
            total_paid=total_paid,
            total_interest_paid=total_interest,
            debts=[debt_summary],
        )

        # 6) Elegir la mejor oferta según intereses (y luego plazo)
        if best_summary is None:
            best_summary = scenario_summary
        else:
            if scenario_summary.total_interest_paid < best_summary.total_interest_paid:
                best_summary = scenario_summary
            elif (
                scenario_summary.total_interest_paid == best_summary.total_interest_paid
                and scenario_summary.total_months < best_summary.total_months
            ):
                best_summary = scenario_summary

    # Si ninguna oferta fue viable, devolvemos un escenario vacío
    if best_summary is None:
        return ScenarioSummary(
            customer_id=portfolio.customer_id,
            scenario_type="consolidation",
            total_months=0,
            total_paid=0.0,
            total_interest_paid=0.0,
            debts=[],
        )

    return best_summary