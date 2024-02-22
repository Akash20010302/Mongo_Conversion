from typing import List
from sqlmodel import SQLModel


class MonthlyIncome(SQLModel):
    month: str
    salary_amount: float
    other_income_amount: float
    overseas_income_amount: float  # New field
    business_income_amount: float  # New field
    personal_income_amount: float  # New field
    total_income_amount: float

class IncomeSources(SQLModel):
    salary_sources: List[str]
    other_income_sources: List[str]
    business_income_sources: List[str]
    personal_income_sources: List[str]
    overseas_income_sources: List[str]  # New field

class IncomeSummaryResponse(SQLModel):
    number_of_salary_accounts: int
    number_of_other_income_accounts: int
    number_of_personal_savings_account: int
    number_of_business_income_accounts: int
    number_of_overseas_acount: int
    red_flag: int
    total_number_of_income_sources: int
    total_salary_received: float
    total_other_income: float
    total_personal_savings: float
    total_overseas_income: float
    total_business_income: float
    total_income: float
    monthly_income_details: List[MonthlyIncome]
    income_sources: IncomeSources
    #ADDED
    # overseas_income_sources: int  # New field
    # overseas_income_amount: float  # New field
    income_percentage: dict
    income_score_percentage: int
    income_score_text: str
    highlights: List[str]
    income_highlights: List[str]
    distribution_highlights: List[str]