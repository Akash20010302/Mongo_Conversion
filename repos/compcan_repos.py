from sqlmodel import Session, select
from models.Company import CompanyList
from loguru import logger
from models.CompCandidateList import CompCanList


def select_all_candidatesid_filtered(companyid: int, session: Session):
    statement = (
        select(CompCanList.id)
        .join(CompanyList)
        .where(CompCanList.isDeleted == False, CompCanList.companyid == companyid)
    )
    res = session.exec(statement).all()
    return res
