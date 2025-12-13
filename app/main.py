import json
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .utils.data_loader import load_all_data

from .models.portfolio import CustomerPortfolio
from .models.scenarios import ScenarioSummary
from .models.scenarios import ScenarioComparisonResult
from .models.report import GeneratedReport

from .services.portfolio_service import build_customer_portfolio
from .services.scenario_minimum_service import simulate_minimum_payment_scenario
from .services.scenario_optimized_service import simulate_optimized_plan
from .services.scenario_consolidation_service import simulate_consolidation_scenario
from .services.scenario_comparison_service import compute_scenarios_overview
from .services.report_generation_service import generate_explanatory_report

import pandas as pd


app = FastAPI(title="Asistente de Reestructuración Financiera")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/datasets/upload")
async def upload_datasets(
    loans: UploadFile = File(...),
    cards: UploadFile = File(...),
    payments_history: UploadFile = File(...),
    credit_score_history: UploadFile = File(...),
    customer_cashflow: UploadFile = File(...),
    bank_offers: UploadFile = File(...),
):
    try:
        def read_csv(upload: UploadFile, name: str) -> pd.DataFrame:
            try:
                upload.file.seek(0)
                df = pd.read_csv(upload.file)
                if df.empty:
                    raise ValueError(f"El archivo '{name}' está vacío.")
                return df
            finally:
                upload.file.close()

        def read_bank_offers_json(upload: UploadFile, name: str):
            try:
                upload.file.seek(0)
                raw = upload.file.read()
                text = raw.decode("utf-8").strip()
                if not text:
                    raise ValueError(f"El archivo JSON '{name}' está vacío.")

                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        data = [data]
                except json.JSONDecodeError:
                    data = [
                        json.loads(line)
                        for line in text.splitlines()
                        if line.strip()
                    ]

                if not isinstance(data, list) or not data:
                    raise ValueError(f"El archivo JSON '{name}' no contiene ofertas válidas.")

                for i, o in enumerate(data):
                    if not isinstance(o, dict):
                        raise ValueError(f"Oferta #{i} en '{name}' no es un objeto JSON válido.")

                return data

            finally:
                upload.file.close()

        new_data = {
            "loans": read_csv(loans, "loans"),
            "cards": read_csv(cards, "cards"),
            "payments_history": read_csv(payments_history, "payments_history"),
            "credit_score_history": read_csv(credit_score_history, "credit_score_history"),
            "customer_cashflow": read_csv(customer_cashflow, "customer_cashflow"),
            "bank_offers": read_bank_offers_json(bank_offers, "bank_offers"),
        }

        app.state.data = new_data

        summary = {name: len(obj) for name, obj in new_data.items()}

        return {
            "status": "ok",
            "message": "Datasets cargados y reemplazados correctamente.",
            "rows_per_dataset": summary,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al procesar los archivos: {e}",
        )

@app.on_event("startup")
def startup_event():
    if not getattr(app.state, "data", None):
        app.state.data = load_all_data()


@app.get("/test")
def test_check():
    keys = list(getattr(app.state, "data", {}).keys())
    return {"status": "ok", "datasets": keys}


@app.get("/customers", response_model=List[str])
def list_customers():
    data = app.state.data
    loans_df = data["loans"]
    cards_df = data["cards"]

    loan_customers = set(loans_df["customer_id"].unique())
    card_customers = set(cards_df["customer_id"].unique())

    customers = sorted(loan_customers.union(card_customers))
    return customers


@app.get("/customers/{customer_id}/portfolio", response_model=CustomerPortfolio)
def get_customer_portfolio(customer_id: str):
    portfolio = build_customer_portfolio(app, customer_id)
    return portfolio


@app.get(
    "/customers/{customer_id}/scenarios/minimum",
    response_model=ScenarioSummary,
)
def get_minimum_payment_scenario(customer_id: str):
    """
    Escenario 1: el cliente paga solo mínimo en tarjetas
    y sigue el plan original en préstamos.
    """
    portfolio = build_customer_portfolio(app, customer_id)
    scenario = simulate_minimum_payment_scenario(portfolio)
    return scenario

@app.get(
    "/customers/{customer_id}/scenarios/optimized",
    response_model=ScenarioSummary,
)
def get_optimized_payment_scenario(customer_id: str):
    """
    Escenario 2: plan optimizado usando el available_cashflow para
    pagar mínimos y luego atacar la deuda más cara.
    """
    portfolio = build_customer_portfolio(app, customer_id)
    scenario = simulate_optimized_plan(portfolio)
    return scenario

@app.get(
    "/customers/{customer_id}/scenarios/consolidation",
    response_model=ScenarioSummary,
)
def get_consolidation_scenario(customer_id: str):
    """
    Escenario 3: Consolidación de deudas usando las ofertas del banco.
    """
    portfolio = build_customer_portfolio(app, customer_id)
    offers_raw = app.state.data["bank_offers"]
    scenario = simulate_consolidation_scenario(portfolio, offers_raw)
    return scenario

@app.get(
    "/customers/{customer_id}/scenarios/overview",
    response_model=ScenarioComparisonResult,
)
def get_scenarios_overview(customer_id: str):
    """
    Devuelve los tres escenarios (mínimo, optimizado, consolidación)
    y el ahorro en intereses y meses de cada uno vs el escenario mínimo.
    """
    overview = compute_scenarios_overview(app, customer_id)
    return overview

@app.get(
    "/customers/{customer_id}/report",
    response_model=GeneratedReport,
)
def get_customer_report(customer_id: str):
    """
    Genera un informe explicativo usando IA generativa
    a partir del portafolio del cliente y el overview de escenarios.
    """

    portfolio = build_customer_portfolio(app, customer_id)

    overview = compute_scenarios_overview(app, customer_id)

    report = generate_explanatory_report(portfolio, overview)

    return report