from sqlmodel import SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")


class AcademicDetailsResponse(SQLModel):
    all_academic_govt_docs : list
    all_academic_tenure: list
    red_flag: int
    discrepancies: int
    highlight: list
    academic_score: int
    academic_score_text: str