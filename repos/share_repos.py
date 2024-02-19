import json
from typing import Optional
from sqlmodel import Session, select
from models.CompCandidateList import CompCanList
from models.Share import Share
from models.Application import ApplicationList


def convert_to_share_list(res, session):
    mapped_data = []
    for x in res:
        res2 = session.get(ApplicationList, x.appid)
        res3 = session.get(CompCanList, res2.compid)
        mapped_item = {
            "id": x.id,
            "email": x.email,
            "shared": x.shared.isoformat(),
            "expiry": x.expiry.isoformat(),
            "firstName": res3.firstName,
            "lastName": res3.lastName,
            "candidatetype": res2.candidatetype,
            "applicationtype": res2.applicationtype,
            "status": x.status,
        }
        mapped_data.append(mapped_item)
    json_data = json.dumps(mapped_data)
    return mapped_data


def get_share_list(session: Session, appid: Optional[list] = None):
    statement = select(Share).where(Share.isDeleted == False)
    if appid is not None:
        statement = statement.where(Share.formid.in_(appid))
    res = session.exec(statement).all()
    if res is not None:
        res = convert_to_share_list(res, session)
    return res
