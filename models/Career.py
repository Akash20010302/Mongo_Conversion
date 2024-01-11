from sqlmodel import SQLModel


class CareerDetailsResponse(SQLModel):
    all_experiences_govt_docs : list
    all_experiences_tenure: list
    good_to_know: int
    red_flag: int
    discrepancies: int
    highlight: list
    career_score: int
    career_score_text: str