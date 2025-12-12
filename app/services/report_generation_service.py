from typing import Optional
import textwrap

from ..models.portfolio import CustomerPortfolio
from ..models.scenarios import ScenarioComparisonResult, ScenarioSavings
from ..models.report import GeneratedReport
from ..services.llm_client import LLMClient


def _find_scenario(
    overview: ScenarioComparisonResult,
    scenario_type: str,
) -> Optional[ScenarioSavings]:
    for s in overview.scenarios:
        if s.scenario_type == scenario_type:
            return s
    return None


def _choose_best_scenario(overview: ScenarioComparisonResult) -> Optional[ScenarioSavings]:
    """
    Elige el mejor escenario distinto al mínimo, priorizando:
      1) Mayor ahorro de intereses
      2) En caso de empate, más meses ahorrados
    """
    candidates = [
        s for s in overview.scenarios
        if s.scenario_type != "minimum_payment"
    ]
    if not candidates:
        return None

    best = candidates[0]
    for s in candidates[1:]:
        if s.interest_savings_vs_minimum > best.interest_savings_vs_minimum:
            best = s
        elif (
            s.interest_savings_vs_minimum == best.interest_savings_vs_minimum
            and s.months_saved_vs_minimum > best.months_saved_vs_minimum
        ):
            best = s
    return best


def _build_report_prompt(
    portfolio: CustomerPortfolio,
    overview: ScenarioComparisonResult,
) -> str:
    """
    Construye el prompt para el modelo generativo usando la info del portafolio
    y las métricas de los escenarios.
    TODO el texto final lo escribe el LLM.
    """
    min_s = _find_scenario(overview, "minimum_payment")
    opt_s = _find_scenario(overview, "optimized_plan")
    cons_s = _find_scenario(overview, "consolidation")
    best_s = _choose_best_scenario(overview)

    if min_s is None:
        raise ValueError("No se encontró escenario mínimo en el overview")

    def r2(x: float) -> float:
        return round(x, 2)

    # Datos básicos del cliente
    customer_id = portfolio.customer_id
    credit_score = portfolio.credit_score
    available_cf = r2(portfolio.cashflow.available_cashflow)
    monthly_income = r2(portfolio.cashflow.monthly_income_avg)
    essential_expenses = r2(portfolio.cashflow.essential_expenses_avg)

    # Resumen numérico por escenario
    min_block = f"""
    Escenario 'minimum_payment' (solo pagos mínimos):
    - total_months: {min_s.total_months}
    - total_paid: {r2(min_s.total_paid)}
    - total_interest_paid: {r2(min_s.total_interest_paid)}
    """

    opt_block = ""
    if opt_s is not None:
        opt_block = f"""
        Escenario 'optimized_plan' (plan optimizado usando flujo de caja):
        - total_months: {opt_s.total_months}
        - total_paid: {r2(opt_s.total_paid)}
        - total_interest_paid: {r2(opt_s.total_interest_paid)}
        - interest_savings_vs_minimum: {r2(opt_s.interest_savings_vs_minimum)}
        - months_saved_vs_minimum: {opt_s.months_saved_vs_minimum}
        """

    if cons_s is not None:
        cons_block = f"""
        Escenario 'consolidation' (consolidación de deudas):
        - total_months: {cons_s.total_months}
        - total_paid: {r2(cons_s.total_paid)}
        - total_interest_paid: {r2(cons_s.total_interest_paid)}
        - interest_savings_vs_minimum: {r2(cons_s.interest_savings_vs_minimum)}
        - months_saved_vs_minimum: {cons_s.months_saved_vs_minimum}
        """
    else:
        cons_block = """
        Escenario 'consolidation':
        - No hay oferta viable de consolidación para este cliente.
        """

    if best_s is not None:
        best_block = f"""
        Escenario recomendado según las métricas:
        - scenario_type: {best_s.scenario_type}
        - interest_savings_vs_minimum: {r2(best_s.interest_savings_vs_minimum)}
        - months_saved_vs_minimum: {best_s.months_saved_vs_minimum}
        """
    else:
        best_block = """
        Escenario recomendado según las métricas:
        - Ningún escenario alternativo mejora de forma clara al pago mínimo.
        """

    num_loans = len(portfolio.loans)
    num_cards = len(portfolio.cards)

    prompt = textwrap.dedent(
        f"""
        Eres un asesor financiero de un banco en Perú. Tu tarea es explicar a un cliente
        de banca de personas, en lenguaje claro, sus alternativas para pagar sus deudas.
        NO menciones que eres un modelo de IA ni uses lenguaje técnico innecesario.

        Información del cliente:
        - customer_id: {customer_id}
        - credit_score: {credit_score}
        - ingresos_mensuales_promedio: {monthly_income}
        - gastos_esenciales_mensuales: {essential_expenses}
        - flujo_de_caja_disponible_mensual (available_cashflow): {available_cf}
        - numero_prestamos (loans): {num_loans}
        - numero_tarjetas (cards): {num_cards}

        Información de escenarios calculados por el motor analítico del banco:

        {min_block}

        {opt_block}

        {cons_block}

        {best_block}

        FORMATO DE SALIDA (MUY IMPORTANTE):
        - Escribe la respuesta en ESPAÑOL.
        - Usa **Markdown simple** con este esquema:

          # Resumen general

          (1–2 párrafos cortos)

          ## Escenario 1 – Pago mínimo

          - Punto 1…
          - Punto 2…
          - etc.

          ## Escenario 2 – Plan organizado con tu flujo de caja

          - Punto 1…
          - Punto 2…
          - etc.

          ## Escenario 3 – Consolidación de deudas

          - Explica la consolidación o indica claramente si no es viable.
          - Menciona plazo, total pagado e intereses.
          - Menciona el ahorro vs pago mínimo si existe.

          ## Recomendación final

          - Indica qué escenario es más conveniente según las métricas.
          - Explica por qué es mejor (intereses ahorrados y meses menos de deuda).
          - Incluye un mensaje empático y práctico.

        INSTRUCCIONES ADICIONALES:
        1. No inventes montos ni plazos nuevos: usa solo los números entregados arriba,
           puedes redondear para hacer el texto más natural sin cambiar el sentido.
        2. Separa claramente cada sección con un título y una línea en blanco.
        3. Usa frases cortas y listas con viñetas para que el texto sea fácil de leer
           en una app móvil.
        4. No menciones palabras internas como "scenario_type", "min_s" o similares;
           usa nombres amigables: "pago mínimo", "plan organizado con tu flujo de caja"
           y "consolidación de deudas".
        5. Genera un único texto en Markdown listo para mostrarse al cliente.
        """
    )

    return prompt


def generate_explanatory_report(
    portfolio: CustomerPortfolio,
    overview: ScenarioComparisonResult,
) -> GeneratedReport:
    """
    Genera un informe explicativo 100% con IA generativa (Azure OpenAI),
    usando los datos del portafolio y los resultados de los escenarios.
    """
    prompt = _build_report_prompt(portfolio, overview)

    llm = LLMClient()
    report_text = llm.generate_text(prompt)

    return GeneratedReport(
        customer_id=portfolio.customer_id,
        language="es",
        report_text=report_text,
    )