import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND
from models.Application import ApplicationList
from models.Form import Form
from models.Share import GetShare, ReShare, Share, ShareEmail, StopShare
from repos.share_repos import get_share_list
from tools.email_tools import get_email_body, send_share_email
from tools.encrypter_tools import decrypt, encrypt
from db.db import session

share_router = APIRouter()


@share_router.post("/send_report",response_model=str, tags=['Share'])
async def send_report(share: ShareEmail):
    failed=[]
    for x in share.email:
        email=dict()
        id = []
        for y in share.id:
            appl_found = session.get(ApplicationList,y)
            form_found = session.get(Form,y)
            if appl_found is not None and form_found is not None:
                now = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30) 
                a=Share(
                    appid = y,
                    app = appl_found,
                    formid = y,
                    form = form_found,
                    email = x,
                    shared = now,
                    expiry = now + datetime.timedelta(days= share.expiry_date)      
                )
                session.add(a)
                session.commit()
                session.refresh(a)
                sharedid = await encrypt({"id":a.id})
                a.sharedid = sharedid
                a.shared_url = share.url+f"/{sharedid}"
                session.add(a)
                session.commit()
                session.refresh(a)
                id.append(a.id)
                name = form_found.firstName + " " + (form_found.middleName + " " if form_found.middleName is not None else "") + form_found.lastName
                email[a.id]=name
        try:
            body = await get_email_body(email,share.emailBody)
            if ((await send_share_email(to_email=x,subject=share.emailSubject,body=body))==True):
                for x in id:
                    a = session.get(Share,x)
                    a.email_status = True
                    session.add(a)
                    session.commit()
            else:
                #logger.debug(x)
                failed.append(x)     
        except Exception as e:
            #logger.debug(e)
            failed.append(x)
    if len(failed)<1:
        return JSONResponse(status_code=HTTP_200_OK,content="All Emails sent successfully")
    else:
       return JSONResponse(status_code=HTTP_400_BAD_REQUEST,content=f"Failed to send emails to : {failed}")



@share_router.get("/check_shared/{key}", tags=['Share'])
async def check_share(key: str):
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
        share_found= session.get(Share,data["id"])
        if share_found is not None:
            #logger.debug(share_found)
            if share_found.expiry>= datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30) and share_found.status=="Active":
                share_found.lastlogin=datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
                session.add(share_found)
                session.commit()
                session.refresh(share_found)
                return share_found.formid
            elif share_found.expiry< datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30) and share_found.status=="Active":
                share_found.status="Expired"
                session.add(share_found)
                session.commit()
                raise ExpiryException
            elif share_found.expiry< datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30) and share_found.status=="Expired":
                raise ExpiryException
            elif share_found.status=="Terminated":
                raise TerminatedException
        else:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Share not found")
    except HTTPException as ht:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Share not found")
    except ExpiryException as ex:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="View Expired.")
    except TerminatedException as tx:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="Report Has Been Stopped Sharing.")
    except Exception as e:
        #logger.debug(e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="Invalid Key.")

@share_router.put("/stop_share/",response_model=str, tags=['Share'])
async def stop_share(id: StopShare):
    share_found= session.get(Share,id.id)
    if share_found is not None:
        share_found.status="Terminated"
        session.add(share_found)
        session.commit()
        return JSONResponse(status_code=HTTP_200_OK,content=f"Stopped sharing to {share_found.email}.")
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,detail="Share not found")

@share_router.put("/reshare/",response_model=str, tags=['Share'])
async def reshare(id: ReShare):
    share_found= session.get(Share,id.id)
    if share_found is not None:
        if share_found.status!="Active":
            share_found.status="Active"
            session.add(share_found)
            session.commit()
            return JSONResponse(status_code=HTTP_200_OK,content=f"Restarted sharing to {share_found.email}.")
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="Already sharing this report.")            
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,detail="Share not found")

@share_router.post("/get-list/", tags=['Share'])
async def stop_share(id: Optional[GetShare] = None):
    share_list = await get_share_list()
    if share_list is not None:
        return share_list