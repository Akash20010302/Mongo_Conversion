import json
from typing import Optional
from sqlmodel import Session, select
from db.db import session
from db.db import engine
from models.CompCandidateList import CompCanList
from models.Share import Share
from models.Application import ApplicationList

async def convert_to_share_list(res):
    mapped_data = []
    for x in res:
        res2 = session.get(ApplicationList,x.appid)
        res3 = session.get(CompCanList,res2.compid)
        mapped_item = {
            "id": x.id,
            "email" : x.email,
            "shared" : x.shared.isoformat(),
            "expiry" : x.expiry.isoformat(),
            "firstName" : res3.firstName,
            "lastName" : res3.lastName,
            "candidatetype" : res2.candidatetype,
            "applicationtype" : res2.applicationtype,
            "status" : x.status
        }
        mapped_data.append(mapped_item)
    json_data = json.dumps(mapped_data)
    return mapped_data

async def get_share_list(appid:Optional[list]=None):
    with Session(engine) as session:
        statement = select(Share).where(Share.isDeleted == False)
        if appid is not None:
            statement =statement.where(Share.formid.in_(appid))
        res= session.exec(statement).all()
        if res is not None:
            res = await convert_to_share_list(res)
        return res