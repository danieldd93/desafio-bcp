from pathlib import Path
from typing import Dict, Any

import pandas as pd
import json


# Carpeta raíz del proyecto (…/desafio-bcp)
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def load_loans() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "loans.csv")


def load_cards() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "cards.csv")


def load_payments_history() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "payments_history.csv")


def load_credit_score_history() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "credit_score_history.csv")


def load_customer_cashflow() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "customer_cashflow.csv")


def load_bank_offers() -> Any:
    with open(DATA_DIR / "bank_offers.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_data() -> Dict[str, Any]:
    """
    Carga todos los datasets y los devuelve en un dict.
    """
    return {
        "loans": load_loans(),
        "cards": load_cards(),
        "payments_history": load_payments_history(),
        "credit_score_history": load_credit_score_history(),
        "customer_cashflow": load_customer_cashflow(),
        "bank_offers": load_bank_offers(),
    }