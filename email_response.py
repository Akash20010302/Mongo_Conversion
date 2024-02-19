from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import env
import smtplib
from loguru import logger
from config import FROM_EMAIL_ID, PASSWORD


def send_email(status_code, api_name):
    message = f"Internal server error in {env}"
    to_mail = ["samiran.dolui@neurologicai.com",
                "someshwar.srimany@neurologicai.com",
                "soulina.mondal@neurologicai.com",
                "nishan@neurologicai.com",
                "sujatha.vn@fxprosinc.com"]
    if status_code == 500:
        for x in to_mail:
            failure = f"{api_name} api Failure"
            email_message = MIMEMultipart()
            email_message["From"] = FROM_EMAIL_ID
            email_message["To"] = x
            email_message["Subject"] = failure
            body = f"""status_code : {status_code}<br>message : {message}"""
            email_message.attach(MIMEText(body, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(FROM_EMAIL_ID, PASSWORD)
                server.sendmail(FROM_EMAIL_ID, x, email_message.as_string())
            logger.debug(f"{api_name} api is not working.")
