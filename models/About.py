from typing import Optional
from pydantic import EmailStr
from sqlmodel import SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")


class HouseholdIncome(SQLModel):
    candidate_monthly_take: float
    spouse_monthly_take: float
    total_family_income: float

class Info(SQLModel):
    application_id: int   #changed
    firstName: str
    middleName: Optional[str]
    lastName: str
    phone: str
    email: EmailStr
    city: Optional[str]
    gender: str
    dob: str
    age: int
    marital_status: str
    spouse_work_status: Optional[str]
    spouse_employer: Optional[str]
    kidsnum: int
    adultdependents: int
    home: bool
    car: bool
    twoWheeler: bool
    creditCard: bool
    Loan: bool
    Investment: bool
    education: str
    education_institute: Optional[str]
    location: Optional[str]
    total_experience: float
    work_industry: str
    skillset: str
    current_role: Optional[str]
    tenure_last_job: int
    household_income: HouseholdIncome