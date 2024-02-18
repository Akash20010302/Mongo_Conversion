import datetime
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from sqlmodel import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_401_UNAUTHORIZED,
)
from auth.auth import AuthHandler
from db.db import get_db_db
from models.Application import ApplicationList
from models.CompCandidateList import CompCanList
from models.Company import CompanyList
from models.Form import Form
from models.Share import ReShare, Share, ShareEmail, StopShare
from repos.application_repos import select_all_appid
from repos.compcan_repos import select_all_candidatesid_filtered
from repos.share_repos import get_share_list
from tools.email_tools import get_email_body, report_share_email
from tools.encrypter_tools import decrypt, encrypt
from sqlalchemy.exc import PendingRollbackError

share_router = APIRouter()
auth_handler = AuthHandler()


@share_router.post("/send_report", tags=["Share"])
async def send_report(share: ShareEmail, session: Session = Depends(get_db_db)):
    failed = []
    for x in share.email:
        email = dict()
        id = []
        for y in share.id:
            appl_found = session.get(ApplicationList, y)
            form_found = session.get(Form, y)
            if appl_found is not None and form_found is not None:
                now = datetime.datetime.utcnow() + datetime.timedelta(
                    hours=5, minutes=30
                )
                a = Share(
                    appid=y,
                    app=appl_found,
                    formid=y,
                    form=form_found,
                    email=x,
                    shared=now,
                    expiry=now + datetime.timedelta(days=share.expiry_date),
                )
                session.add(a)
                session.commit()
                session.refresh(a)
                sharedid = await encrypt({"id": a.id, "iat": now})
                a.sharedid = sharedid
                a.shared_url = share.url + f"/{sharedid}"
                session.add(a)
                session.commit()
                session.refresh(a)
                id.append(a.id)
                name = (
                    form_found.firstName
                    + " "
                    + (
                        form_found.middleName + " "
                        if form_found.middleName is not None
                        else ""
                    )
                    + form_found.lastName
                )
                email[a.id] = [name, appl_found.candidatetype]
        try:
            body = await get_email_body(email, session)
            if (
                await report_share_email(
                    to_email=x,
                    companyname=session.get(
                        CompanyList,
                        session.get(CompCanList, appl_found.compid).companyid,
                    ).legalname,
                    body=body,
                    emailbody=share.emailBody,
                )
            ) == True:
                for x in id:
                    a = session.get(Share, x)
                    a.email_status = True
                    session.add(a)
                    session.commit()
            else:
                # logger.debug(x)
                failed.append(x)
        except Exception as e:
            logger.error(e)
            failed.append(x)
    if len(failed) < 1:
        return JSONResponse(
            status_code=HTTP_200_OK, content={"body": "All Emails sent successfully"}
        )
    else:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"body": f"Failed to send emails to : {failed}"},
        )


@share_router.get("/check_shared/{key}", tags=["Share"])
async def check_share(key: str, session: Session = Depends(get_db_db)):
    class InvalidToken(Exception):
        def __init__(self, message="Invalid Token"):
            self.message = message
            super().__init__(self.message)

    class ExpiryException(Exception):
        def __init__(self, message="View Expired"):
            self.message = message
            super().__init__(self.message)

    class TerminatedException(Exception):
        def __init__(self, message="View Expired"):
            self.message = message
            super().__init__(self.message)

    try:
        data = await decrypt(key)
        share_found = session.get(Share, data["id"])
        # logger.debug(f'''{data.get("id")}''')
        if share_found is not None:
            appl_found = session.get(ApplicationList, share_found.appid)
            if appl_found is not None:
                # logger.debug(share_found)
                if (
                    share_found.expiry
                    >= datetime.datetime.utcnow()
                    + datetime.timedelta(hours=5, minutes=30)
                    and share_found.status == "Active"
                ):
                    share_found.lastlogin = (
                        datetime.datetime.utcnow()
                        + datetime.timedelta(hours=5, minutes=30)
                    )
                    session.merge(share_found)
                    session.commit()
                    session.refresh(share_found)
                    return JSONResponse(
                        status_code=HTTP_200_OK,
                        content={
                            "id": share_found.formid,
                            "candidatetype": appl_found.candidatetype,
                        },
                    )
                elif (
                    share_found.expiry
                    < datetime.datetime.utcnow()
                    + datetime.timedelta(hours=5, minutes=30)
                    and share_found.status == "Active"
                ):
                    share_found.status = "Expired"
                    session.merge(share_found)
                    session.commit()
                    raise ExpiryException
                elif (
                    share_found.expiry
                    < datetime.datetime.utcnow()
                    + datetime.timedelta(hours=5, minutes=30)
                    and share_found.status == "Expired"
                ):
                    raise ExpiryException
                elif share_found.status == "Terminated":
                    raise TerminatedException
            else:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND, detail="Application not found"
                )
        else:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Share not found"
            )
    except PendingRollbackError as pre:
        session.rollback()
        await check_share(key)
    except InvalidToken as ie:
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid Key.")
    except HTTPException as ht:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Share not found")
    except ExpiryException as ex:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="View Expired.")
    except TerminatedException as tx:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Report Has Been Stopped Sharing."
        )
    except Exception as e:
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid Key.")


@share_router.put("/shared/stop_share", response_model=str, tags=["Share"])
async def stop_share(id: StopShare, session: Session = Depends(get_db_db)):
    share_found = session.get(Share, id.id)
    if share_found is not None:
        share_found.status = "Terminated"
        session.add(share_found)
        session.commit()
        return JSONResponse(
            status_code=HTTP_200_OK, content=f"Stopped sharing to {share_found.email}."
        )
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Share not found")


@share_router.put("/shared/reshare", response_model=str, tags=["Share"])
async def reshare(id: ReShare, session: Session = Depends(get_db_db)):
    share_found = session.get(Share, id.id)
    if share_found is not None:
        if share_found.status != "Active":
            share_found.status = "Active"
            session.add(share_found)
            session.commit()
            return JSONResponse(
                status_code=HTTP_200_OK,
                content=f"Restarted sharing to {share_found.email}.",
            )
        else:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Already sharing this report."
            )
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Share not found")


@share_router.get(f"/shared/get-list", tags=["Share"])
async def get_share(
    user=Depends(auth_handler.get_current_admin), session: Session = Depends(get_db_db)
):
    try:
        if user.role not in ["Super Admin", "Admin"]:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized Access"
            )
        if user.role == "Super Admin":
            share_list = get_share_list(session)
            if share_list is not None:
                return share_list
            else:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail="Nothing Shared"
                )
        elif user.role == "Admin":
            comcanlist_found = select_all_candidatesid_filtered(user.companyid, session)
            if comcanlist_found is None or len(comcanlist_found) < 0:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail="No Candidate Present."
                )
            appl_list = select_all_appid(comcanlist_found, session)
            if appl_list is None or len(appl_list) < 0:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail="No Application Present."
                )
            # logger.debug(appl_list)
            share_list = get_share_list(session, appl_list)
            if share_list is not None:
                return share_list
            else:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail="Nothing Shared"
                )
        else:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Unknown Error"
            )
    except PendingRollbackError as pre:
        session.rollback()
        await get_share()
