from typing import Optional
from fastapi import HTTPException

from ..models.portfolio import (
    LoanItem,
    CardItem,
    CustomerCashflow,
    CustomerPortfolio,
    PaymentHistoryItem,   
    CreditScoreRecord,  
    BankOffer,         
)


def build_customer_portfolio(app, customer_id: str) -> CustomerPortfolio:
    data = app.state.data

    loans_df = data["loans"]
    cards_df = data["cards"]
    credit_df = data["credit_score_history"]
    cashflow_df = data["customer_cashflow"]
    # payments_df = data["payments_history"]

    # --- Loans ---
    customer_loans = loans_df[loans_df["customer_id"] == customer_id]

    loan_items = [
        LoanItem(
            loan_id=row["loan_id"],
            customer_id=row["customer_id"],
            product_type=row["product_type"],
            principal=float(row["principal"]),
            annual_rate_pct=float(row["annual_rate_pct"]),
            remaining_term_months=int(row["remaining_term_months"]),
            collateral=str(row["collateral"]).lower() == "true",
            days_past_due=int(row["days_past_due"]),
        )
        for _, row in customer_loans.iterrows()
    ]

    # --- Cards ---
    customer_cards = cards_df[cards_df["customer_id"] == customer_id]

    card_items = [
        CardItem(
            card_id=row["card_id"],
            customer_id=row["customer_id"],
            balance=float(row["balance"]),
            annual_rate_pct=float(row["annual_rate_pct"]),
            min_payment_pct=float(row["min_payment_pct"]),
            payment_due_day=int(row["payment_due_day"]),
            days_past_due=int(row["days_past_due"]),
        )
        for _, row in customer_cards.iterrows()
    ]

    if not loan_items and not card_items:
        raise HTTPException(status_code=404, detail="Customer not found or no debts")

    # --- Credit score: último registro por fecha ---
    customer_credit = credit_df[credit_df["customer_id"] == customer_id]
    credit_score: Optional[int] = None
    if not customer_credit.empty:
        customer_credit_sorted = customer_credit.sort_values("date")
        credit_score = int(customer_credit_sorted.iloc[-1]["credit_score"])

    # --- Cashflow ---
    customer_cf = cashflow_df[cashflow_df["customer_id"] == customer_id]
    if customer_cf.empty:
        raise HTTPException(
            status_code=404,
            detail="Cashflow data not found for customer",
        )

    cf_row = customer_cf.iloc[0]
    monthly_income = float(cf_row["monthly_income_avg"])
    essential_expenses = float(cf_row["essential_expenses_avg"])
    income_variability = float(cf_row["income_variability_pct"])

    available_cashflow = max(monthly_income - essential_expenses, 0.0)

    cashflow = CustomerCashflow(
        customer_id=customer_id,
        monthly_income_avg=monthly_income,
        income_variability_pct=income_variability,
        essential_expenses_avg=essential_expenses,
        available_cashflow=available_cashflow,
    )

    portfolio = CustomerPortfolio(
        customer_id=customer_id,
        credit_score=credit_score,
        loans=loan_items,
        cards=card_items,
        cashflow=cashflow,
    )

    return portfolio