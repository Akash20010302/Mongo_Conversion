import datetime
from typing import List, Optional
from pydantic import EmailStr
from sqlmodel import SQLModel
import warnings

from db.db import get_db_analytics,get_db_backend

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class SummaryBasicInfo(SQLModel):
    firstName: str = 'N/A'
    middleName : str = 'N/A'
    lastName : str = 'N/A'
    phone : str = 'N/A'
    email : EmailStr = 'N/A'
    age : int = 'N/A'
    gender : str = 'N/A'
    marital_status : str = 'N/A'
    city : str = 'N/A'
    role : str = 'N/A'
    company : str = 'N/A'
    legalname : str = 'N/A'
    report_date : Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
    
    class Config:
        from_attributes = True

class Ideal_ctc(SQLModel):
    lower:int
    upper: int

class offered_past_ctc_summary(SQLModel):
    declared_past_ctc: int
    declared_past_ctc_remark: str
    most_likely_past_ctc: int
    highlight_1: str
    offered_ctc: int
    offered_ctc_remark: str
    ideal_ctc_band: Ideal_ctc
    highlight_2: str

class declared_household_income_summary(SQLModel):
    candidate_ctc: int
    spouse_ctc: int
    household_ctc: int
    mostlikely_expense: int
    highlight: str

class Mobile_(SQLModel):
    remark: str
    issue: str

class Email_(SQLModel):
    remark: str
    issue: str

class Address_(SQLModel):
    remark: str
    issue: str
class Name_(SQLModel):
    remark: str
    issue: str

class contact_information(SQLModel):
    name: Name_
    mobile: Mobile_
    email: Email_
    address: Address_
    highlight_1: Optional[str]
    highlight_2: Optional[str]
        
class identity_info(SQLModel):
    pan_issue: int
    aadhar_issue: int
    highlight: Optional[str] = None
    pan_text:Optional[str] = None
    aadhar_text: Optional[str] = None
        
class IncomePosition(SQLModel):
    total_income: int
    salary_income: int
    salary_text: str
    salary_percentage: int
    business_income: int
    business_percentage: int
    overseas_income: int
    overseas_percentage: int
    personal_income: int
    personal_income_percentage: int
    other_income: int
    other_income_percentage: int
    highlights: List[str]
    
class ExperienceSummary(SQLModel):
    total_experience: int
    median_tenure: float
    median_tenure_text: str
    dual_employment: int
    dual_employment_text: str
    overlapping_contract: int
    overlapping_contract_text: str
    tenure_highlights: str
    exp_highlights: List[str]
        
class Summary(SQLModel):
    income_position:IncomePosition
    experience_summary: ExperienceSummary
    ctc_summary: offered_past_ctc_summary
    household_income_summary: declared_household_income_summary
    contact: contact_information
    identity: identity_info

class AsyncGenerator():
    def __init__(self):
        self.backend = get_db_backend()
        self.analytics = get_db_analytics()