from typing import Optional
from sqlmodel import SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class estimatedExpense(SQLModel):
    lower:int
    upper: int

class IdealCtcBand(SQLModel):
    lower: int
    upper: int
    
class CtcResponse(SQLModel):
    #offeredctc: str
    #currentctc: str
    #difference: Optional[float]
    #change_in_ctc: float
    #change_percent: float
    ctc_benchmark_analysis: list
    offeredctc: str
    ideal_ctc_band: IdealCtcBand
    past_ctc: str
    change_in_ctc: float
    ctc_growth: list
    highlight: str

class NewResponse(SQLModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: estimatedExpense
    MostLikelyExpense: int
    E_IRatio: float

class PreviousResponse(SQLModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: estimatedExpense
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
    avg_tenure: int 
    median_tenure: int
    Risk: str
    remarks: str
    total_exp: float
    num_of_jobs: int
    calculated_work_exp: Optional[float]=0.0


class Response(SQLModel):
    ctc_offered: CtcResponse
    pay_analysis: PayAnalysis
    Expense_income_analysis: ExpenseIncomeAnalysis
    Tenure_analysis: TenureAnalysis