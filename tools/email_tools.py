import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from fastapi import HTTPException, status, Request
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from mysqlx import Session
from models.Share import Share


FROM_EMAIL_ID = "noreply@itraceu.com"
PASSWORD = "nyqysmzachhkerfk"

import datetime
import jwt


async def render_template(template_path, context):
    loader = FileSystemLoader(searchpath="./")
    env = Environment(loader=loader)
    template = env.get_template(template_path)
    return template.render(context)

async def report_share_email(to_email,companyname,body,emailbody):
    try:
        subject = f"{companyname} has shared candidate reports with you"
        context = {
        'company': companyname,
        'body' : body,
        'emailbody':emailbody
        }
        body = await render_template("html-template/slide7.html", context)
        #logger.debug(f"body:{body}")
        from_email = FROM_EMAIL_ID
        password = PASSWORD
        
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "html"))
        
        loop = asyncio.get_event_loop()
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            await loop.run_in_executor(None, server.login, from_email, password)
            await loop.run_in_executor(None, server.sendmail, from_email, to_email, message.as_string())
        return True
    except Exception as ex:
        logger.error(f"Email Error : {ex}")
        return False
# No-8.
# to admin about report share initiation
async def report_share_to_admin_email(to_email):
    try:
        subject = f"Report Sharing has been initiated"
        context = {
        
    }
        body = await render_template("html-template/slide8.html", context)
        #logger.debug(f"body:{body}")
        from_email = FROM_EMAIL_ID
        password = PASSWORD
        
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "html"))
        
        loop = asyncio.get_event_loop()
        
        # Connect and send mail using the loop
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            await loop.run_in_executor(None, server.login, from_email, password)
            await loop.run_in_executor(None, server.sendmail, from_email, to_email, message.as_string())
        return True
    except Exception as ex:
        logger.error(f"Email Error : {ex}")
        return False
  

# async def send_share_email(to_email,subject,body)->bool:
#     try:
#         subject = f"{subject}"
#         body = f'''
#             {body}<br>
#         '''
#         from_email = FROM_EMAIL_ID 
#         password = PASSWORD

#         message = MIMEMultipart()
#         message['From'] = from_email
#         message['To'] = to_email
#         message['Subject'] = subject

#         message.attach(MIMEText(body, 'html'))

#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(from_email, password)
#             server.sendmail(from_email, to_email, message.as_string())
#         return True
#     except Exception as ex:
#         return False

# async def link_generator(id:int,name:str,session:Session)->str:
#     share_found = session.get(Share,id)
#     body = f'''
#             <br><br><strong>{name}</strong><br>
#             Click the View Report to view {name} Report.<br>
#             <a href="{share_found.shared_url}" style="background-color: #03A9F4; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;">View Report</a><br>
#             If the button is not working, you can also click here: <a href="{share_found.shared_url}">{share_found.shared_url}</a><br>
#         '''
#     return body

async def link_generator(id:int,name:str,candidatetype:str,session:Session)->str:
    share_found = session.get(Share,id)
    body = f'''
        <li>
            <div style="font-size: 12px; margin-bottom: 7px;">
                {name} as {candidatetype}
            </div>
            <div style="width: 52%; margin: 0px 0px 25px 7px;">
                <a style="cursor: pointer;
                        font-weight: 600;
                        font-size: 12px;
                        background-color: #1fb100;
                        border: none;
                        color: white;
                        padding: 3px 32px;
                        font-family: 'Poppins', sans-serif;  
                        text-decoration: none; " href="{share_found.shared_url}">View report</a>
            </div>
        </li>
        '''
    return body
# async def get_email_body(email:dict,body:str,session:Session)->str:
#     s='''<br><br>'''
#     for x in email.keys():
#         s+=await link_generator(x,email[x][0],email[x][1],session=session)
#     return body+s
    
async def get_email_body(email:dict,session:Session)->str:
    s=''
    for x in email.keys():
        s+=await link_generator(x,email[x][0],email[x][1],session=session)
    return s      