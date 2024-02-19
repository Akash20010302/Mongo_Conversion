from sqlmodel import Session, select
from db.db import analytics_engine
from models.Kyc import epfo_get_kyc_details


async def find_kyc(id: int):
    with Session(analytics_engine) as session:
        statement = select(epfo_get_kyc_details).where(
            epfo_get_kyc_details.application_id == id
        )
        res = session.exec(statement).first()
        return res
