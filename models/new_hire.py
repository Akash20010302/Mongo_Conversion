from sqlmodel import SQLModel


class Info(SQLModel):
    declared_ctc_accuracy: int
    remark: str
    declared_past_ctc: int
    estimated_ctc_range: str
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

class Response(SQLModel):
    info: Info
    graph: Graph


