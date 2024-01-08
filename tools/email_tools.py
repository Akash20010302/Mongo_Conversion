import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from fastapi import HTTPException, status, Request
from db.db import session
from models.Share import Share


FROM_EMAIL_ID = "noreply@itraceu.com"
PASSWORD = "nyqysmzachhkerfk"

import datetime
import jwt
async def validate_email_token(request: Request):
    EMAIL_API_SECRET_KEY = "trace_app_secret_key_email"
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is missing")
    payload = {
        "user_id": "12345",  # Example user ID
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Expiration time
        }
    og_token = jwt.encode(payload, EMAIL_API_SECRET_KEY, algorithm="HS256")
    

async def send_share_email(to_email,subject,body)->bool:
    try:
        subject = f"{subject}"
        # Use triple quotes for a multi-line string to make it easier to format
        body = f'''
            {body}<br>
        '''
        from_email = FROM_EMAIL_ID  # Replace with your email
        password = PASSWORD  # Replace with your email password or app-specific password

        message = MIMEMultipart()
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject

        message.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, message.as_string())
        return True
    except Exception as ex:
        return False

async def link_generator(id:int,name:str)->str:
    share_found = session.get(Share,id)
    body = f'''
            <br><br><strong>{name}</strong><br>
            Click the View Report to view {name} Report.<br>
            <a href="{share_found.shared_url}" style="background-color: #03A9F4; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;">View Report</a><br>
            If the button is not working, you can also click here: <a href="{share_found.shared_url}">{share_found.shared_url}</a><br>
        '''
    return body


async def get_email_body(email:dict,body:str)->str:
    s='''<br><br>'''
    for x in email.keys():
        s+=await link_generator(x,email[x])
    return body+s
    
       