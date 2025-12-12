from typing import List, Optional, Literal
from pydantic import BaseModel

class LoanItem(BaseModel):
    loan_id: str
    customer_id: str
    product_type: Literal["personal", "micro"]
    principal: float
    annual_rate_pct: float
    remaining_term_months: int
    collateral: bool
    days_past_due: int


class CardItem(BaseModel):
    card_id: str
    customer_id: str
    balance: float
    annual_rate_pct: float
    min_payment_pct: float
    payment_due_day: int
    days_past_due: int


class PaymentHistoryItem(BaseModel):
    product_id: str
    product_type: Literal["loan", "card"]
    customer_id: str
    date: str
    amount: float


class CreditScoreRecord(BaseModel):
    customer_id: str
    date: str                 
    credit_score: int


class CustomerCashflow(BaseModel):
    customer_id: str
    monthly_income_avg: float
    income_variability_pct: float
    essential_expenses_avg: float
    available_cashflow: float 


class BankOffer(BaseModel):
    offer_id: str
    product_types_eligible: List[str]
    max_consolidated_balance: float
    new_rate_pct: float
    max_term_months: int
    conditions: str


class CustomerPortfolio(BaseModel):
    customer_id: str
    credit_score: Optional[int]
    loans: List[LoanItem]
    cards: List[CardItem]
    cashflow: CustomerCashflow