from sqlmodel import SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class CtcRange(SQLModel):
    lower: int
    upper: int
    
    
class Info(SQLModel):
    declared_ctc_accuracy: int
    remark: str
    declared_past_ctc: int
    estimated_ctc_range: CtcRange
    most_likely_past_ctc: int
    gap: int
    highlight: str

class Graph(SQLModel):
    gross_salary: int
    bonus: int
    provident_fund: int
    possible_ctc_variation: int
    most_likely_ctc: int
    declared_ctc: int
    gap: int
    gap_percentage: int

class Response(SQLModel):
    info: Info
    graph: Graph


