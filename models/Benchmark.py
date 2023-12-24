from typing import Optional
from sqlmodel import SQLModel


class CtcResponse(SQLModel):
    offeredctc: str
    currentctc: str
    difference: Optional[float]
    change_in_ctc: float
    change_percent: float

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
    prev: PreviousResponse
    new_: NewResponse
    change_: ChangeResponse
    Risk: str
    remarks: str

class PayAnalysis(SQLModel):
    previous_pay: tuple
    current_offer: tuple
    Risk: str
    remarks: str


class TenureAnalysis(SQLModel):
    work_exp : list
    overlapping_durations: list
    gaps: list
    avg_tenure: float
    median_tenure: float
    Risk: str
    remarks: str


class Response(SQLModel):
    ctc_offered: CtcResponse
    pay_analysis: PayAnalysis
    Expense_income_analysis: ExpenseIncomeAnalysis
    Tenure_analysis: TenureAnalysis