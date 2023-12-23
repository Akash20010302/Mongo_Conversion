from sqlmodel import Session, select
from db.db import analytics_engine
from models.Kyc import Get_Kyc_Details

async def find_kyc(id:int):
    with Session(analytics_engine) as session:
        statement = select(Get_Kyc_Details).where(Get_Kyc_Details.person_id == id)
        res= session.exec(statement).first()
        return res