from typing import List, Tuple

from ..models.portfolio import CustomerPortfolio
from ..models.scenarios import ScenarioSummary, DebtAmortizationSummary


def _monthly_rate(annual_rate_pct: float) -> float:
    """Convierte tasa anual en tasa mensual decimal."""
    return (annual_rate_pct / 100.0) / 12.0


def _loan_monthly_payment(principal: float, annual_rate_pct: float, term_months: int) -> float:
    """
    Calcula la cuota fija de un préstamo con fórmula de anualidad.
    La usaremos como "pago mínimo contractual" del loan.
    """
    r = _monthly_rate(annual_rate_pct)
    n = term_months

    if n <= 0:
        return principal  # caso raro: si el plazo es 0, pagar todo

    if r == 0:
        return principal / n

    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def _card_minimum_payment(balance: float, annual_rate_pct: float, min_payment_pct: float) -> float:
    """
    Pago mínimo de tarjeta:
      - porcentaje sobre saldo
      - nunca menor que 10
      - debe cubrir al menos intereses + algo de capital
    """
    r = _monthly_rate(annual_rate_pct)
    interest = balance * r
    raw_min = balance * (min_payment_pct / 100.0)
    payment = max(raw_min, interest + 1.0, 10.0)

    # no pagar más de lo que se debe + intereses de este mes
    return min(payment, balance + interest)


def simulate_optimized_plan(portfolio: CustomerPortfolio) -> ScenarioSummary:
    """
    Escenario 2: Plan optimizado.

    Regla:
      - Cada mes el cliente dispone de `available_cashflow` para pagar deudas.
      - Primero paga los mínimos de todos los productos (loans + cards).
      - Con lo que sobra, ataca la deuda con tasa más alta (y en caso de empate,
        podrías priorizar las que estén en mora; aquí lo hacemos por tasa).
      - Repite hasta que todas las deudas se cancelan o se llega a un máximo de meses.
    """

    available = portfolio.cashflow.available_cashflow
    if available <= 0:
        # Si no hay flujo disponible, no hay mucho que optimizar…
        # devolvemos algo trivial
        return ScenarioSummary(
            customer_id=portfolio.customer_id,
            scenario_type="optimized_plan",
            total_months=0,
            total_paid=0.0,
            total_interest_paid=0.0,
            debts=[],
        )

    # --------- Estado inicial por deuda ---------
    # Creamos una estructura interna genérica para loans y cards.
    debts_state = []

    # Loans
    for loan in portfolio.loans:
        monthly_min = _loan_monthly_payment(
            principal=loan.principal,
            annual_rate_pct=loan.annual_rate_pct,
            term_months=loan.remaining_term_months,
        )
        debts_state.append(
            {
                "product_id": loan.loan_id,
                "product_type": "loan",
                "rate_annual": loan.annual_rate_pct,
                "balance": float(loan.principal),
                "min_payment": monthly_min,
                "days_past_due": loan.days_past_due,
                "total_paid": 0.0,
                "total_interest": 0.0,
                "months": 0,
            }
        )

    # Cards
    for card in portfolio.cards:
        # El mínimo de tarjeta se recalcula cada mes según el saldo,
        # así que aquí solo dejamos None y lo calculamos en el loop.
        debts_state.append(
            {
                "product_id": card.card_id,
                "product_type": "card",
                "rate_annual": card.annual_rate_pct,
                "balance": float(card.balance),
                "min_payment_pct": card.min_payment_pct,
                "days_past_due": card.days_past_due,
                "total_paid": 0.0,
                "total_interest": 0.0,
                "months": 0,
            }
        )

    # --------- Simulación mes a mes ---------
    max_months = 600  # tope de seguridad para no irnos al infinito
    month = 0

    while month < max_months:
        # Verificamos si ya no queda deuda
        if all(d["balance"] <= 0.01 for d in debts_state):
            break

        month += 1

        # 1) Calcular pagos mínimos y aplicar intereses
        min_total = 0.0
        per_debt_min: List[Tuple[int, float, float]] = []  # (idx, interest, min_payment)

        for idx, d in enumerate(debts_state):
            balance = d["balance"]
            if balance <= 0.01:
                per_debt_min.append((idx, 0.0, 0.0))
                continue

            r = _monthly_rate(d["rate_annual"])
            interest = balance * r

            if d["product_type"] == "loan":
                min_payment = d["min_payment"]
                # no pagar más de balance + intereses
                min_payment = min(min_payment, balance + interest)
            else:  # card
                min_payment = _card_minimum_payment(
                    balance=balance,
                    annual_rate_pct=d["rate_annual"],
                    min_payment_pct=d["min_payment_pct"],
                )

            per_debt_min.append((idx, interest, min_payment))
            min_total += min_payment

        # 2) Si la suma de mínimos supera el cash disponible, escalamos proporcionalmente
        cash_available = available
        scale_factor = 1.0
        if min_total > cash_available and min_total > 0:
            scale_factor = cash_available / min_total

        # 3) Aplicar pagos mínimos (escalados si es necesario)
        cash_available -= min_total * scale_factor

        for idx, interest, min_payment in per_debt_min:
            if min_payment == 0:
                continue

            d = debts_state[idx]
            effective_payment = min_payment * scale_factor

            if effective_payment <= 0:
                continue

            # No pagar más de balance + intereses
            max_this_month = d["balance"] + interest
            if effective_payment > max_this_month:
                effective_payment = max_this_month

            principal_payment = max(effective_payment - interest, 0.0)
            d["balance"] -= principal_payment
            if d["balance"] < 0:
                d["balance"] = 0.0

            d["total_paid"] += effective_payment
            d["total_interest"] += interest if effective_payment > 0 else 0.0
            d["months"] += 1

        # 4) Con el sobrante, atacar la deuda con tasa más alta
        # (si hay varias, tomamos la primera con esa tasa)
        while cash_available > 0.01 and any(d["balance"] > 0.01 for d in debts_state):
            # ordenamos por tasa anual descendente (más alto primero)
            # podrías agregar un bonus por mora si quieres
            debts_sorted = sorted(
                [d for d in debts_state if d["balance"] > 0.01],
                key=lambda x: x["rate_annual"],
                reverse=True,
            )
            target = debts_sorted[0]
            extra = min(cash_available, target["balance"])

            target["balance"] -= extra
            target["total_paid"] += extra
            # el extra se va 100% a capital (ya calculamos intereses del mes)
            cash_available -= extra

    # --------- Construir resumen final ---------
    debt_summaries: List[DebtAmortizationSummary] = []

    for d in debts_state:
        if d["total_paid"] == 0 and d["balance"] <= 0.01:
            # deuda que nunca se pagó porque ya estaba en 0, la omitimos
            continue

        debt_summaries.append(
            DebtAmortizationSummary(
                product_id=d["product_id"],
                product_type=d["product_type"],
                starting_balance=d["total_paid"] + d["balance"] - d["total_interest"]
                if d["months"] > 0
                else d["balance"],
                total_paid=d["total_paid"],
                total_interest_paid=d["total_interest"],
                months_to_payoff=d["months"],
            )
        )

    total_months = max((d.months_to_payoff for d in debt_summaries), default=0)
    total_paid = sum(d.total_paid for d in debt_summaries)
    total_interest = sum(d.total_interest_paid for d in debt_summaries)

    return ScenarioSummary(
        customer_id=portfolio.customer_id,
        scenario_type="optimized_plan",
        total_months=total_months,
        total_paid=total_paid,
        total_interest_paid=total_interest,
        debts=debt_summaries,
    )