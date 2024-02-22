import datetime
from typing import List, Optional, Tuple
from sqlmodel import SQLModel

DateEmailTuple = Tuple[datetime.date, str]  # (date, email)
DatePhoneTuple = Tuple[datetime.date, str]  # (date, phone)
DateAddressTuple = Tuple[datetime.date, str]  # (date, address)

class Enquiries(SQLModel):
    queries_last_1_month: int
    queries_last_3_months: int
    queries_last_6_months: int
    queries_last_12_months: int
    queries_last_24_months: int

class tradeline(SQLModel):
    count: int
    balance: int
    high_credit: int
    credit_limit: int
    past_due: int

class CombinedResponseModel(SQLModel):
    active_accounts: List[str]
    enquiries: Enquiries
    active_account_count: int
    number_of_closed_accounts: int
    total_balance: float
    total_credit_limit: float
    total_past_due: float
    credit_score: int
    tradeline_summary_installment: tradeline
    tradeline_summary_open: tradeline
    tradeline_summary_close: tradeline
    tradeline_summary_total: tradeline
    phone_numbers: List[DatePhoneTuple]
    addresses: List[DateAddressTuple]
    email_addresses: List[DateEmailTuple]
    score_factors: List[str]
