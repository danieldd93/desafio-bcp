from pydantic import BaseModel


class GeneratedReport(BaseModel):
    customer_id: str
    language: str = "es"
    report_text: str