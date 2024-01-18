import json
from typing import Optional
from sqlmodel import Session, select
from models.Company import CompanyList
from loguru import logger
from db.db import engine
from models.CompCandidateList import CompCanList

async def select_all_candidatesid_filtered(companyid):
    with Session(engine) as session:
        statement = select(CompCanList.id).join(CompanyList).where(CompCanList.isDeleted == False, CompCanList.companyid == companyid)
        res = session.exec(statement).all()
        return res