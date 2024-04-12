from sqlmodel import Session, select
from db.db import analytics_engine
from models.Kyc import epfo_get_kyc_details
from models.Kyc import Panlite_data, itr_download_profile

# async def find_kyc(id: int):
#     with Session(analytics_engine) as session:
#         statement = select(epfo_get_kyc_details).where(
#             epfo_get_kyc_details.application_id == id
#         )
#         res = session.exec(statement).first()
#         return res

    
async def find_kyc(id: int):
    with Session(analytics_engine) as session:
        statement = select(itr_download_profile).where(
            itr_download_profile.application_id == id
        )
        res = session.exec(statement).first()
        return res

async def find_panlite(id:int):
    with Session(analytics_engine) as session:
        statement = select(Panlite_data).where(Panlite_data.application_id == id)
        res= session.exec(statement).first()
        return res    