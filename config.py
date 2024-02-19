import os
from dotenv import load_dotenv
load_dotenv()

env = os.getenv("ENV")
FROM_EMAIL_ID = os.getenv("FROM_EMAIL_ID")
PASSWORD = os.getenv("PASSWORD")