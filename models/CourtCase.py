from typing import List, Optional
from sqlmodel import SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")


class CourtCase(SQLModel):
    court_case_type: str
    address: Optional[str] = "Not Available" 
    name: str
    case_year: Optional[str] = "Not Available"
    court_address: Optional[str] = "Not Available"
    case_no: Optional[str] = "Not Available"
    filing_no: Optional[str] = "Not Available"
    registration_no: Optional[str] = "Not Available"
    status: Optional[str] = "Not Available"
    order_summary: Optional[str] = "Not Available"
    first_hearing: Optional[str] = "Not Available"
    next_hearing: Optional[str] = "Not Available"
    decision: Optional[str] = "Not Available"
    police_station: Optional[str] = "Not Available"
    case_type: Optional[str] = "Not Available"
    under_act: Optional[str] = "Not Available"
    fir_no: Optional[str] = "Not Available"
    under_section: Optional[str] = "Not Available"
    case_category: Optional[str] = "Not Available"

class Index(SQLModel):
    legal_position: int
    legal_position_text: str
    civil: int
    criminal: int
    highlight: List[str]


class Response(SQLModel):
    index: Index
    cases: Optional[List[CourtCase]]
    