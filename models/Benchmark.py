from typing import Optional
from sqlmodel import SQLModel


class CtcResponse(SQLModel):
    #offeredctc: str
    #currentctc: str
    #difference: Optional[float]
    #change_in_ctc: float
    #change_percent: float
    ctc_benchmark_analysis: list
    offeredctc: str
    past_ctc: str
    change_in_ctc: float
    ctc_growth: list
    highlight: str

class NewResponse(SQLModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: str
    MostLikelyExpense: int
    E_IRatio: float

class PreviousResponse(SQLModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: str
    MostLikelyExpense: int
    E_IRatio: float

class ChangeResponse(SQLModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: str
    MostLikelyExpense: int
    E_IRatio: float

class ExpenseIncomeAnalysis(SQLModel):
    expense_income_ratio: list
    total_household_income: int
    most_likely_expense: int
    highlights: str
    prev: PreviousResponse
    new_: NewResponse
    change_: ChangeResponse
    #Risk: str
    #remarks: str

class PayAnalysis(SQLModel):
    previous_pay: tuple
    current_offer: tuple
    highlight_1: str
    highlight_2: str


class TenureAnalysis(SQLModel):
    work_exp : list
    overlapping_durations: list
    gaps: list
    avg_tenure: float
    median_tenure: float
    Risk: str
    remarks: str
    total_exp: int
    num_of_jobs: int


class Response(SQLModel):
    ctc_offered: CtcResponse
    pay_analysis: PayAnalysis
    Expense_income_analysis: ExpenseIncomeAnalysis
    Tenure_analysis: TenureAnalysis