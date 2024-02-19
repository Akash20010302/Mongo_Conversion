import boto3
import os
import base64
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()


bucket = os.getenv("BUCKET_NAME")
s3 = boto3.client("s3")


async def upload_file_to_s3(file, dest_name):
    s3.upload_fileobj(file, bucket, dest_name)
    return True


async def parse_s3_url(url):
    # Split the URL by '.s3.' and then by 'amazonaws.com/'
    parts = url.split(".s3.")
    domain_and_key = parts[1].split(".amazonaws.com/")
    bucket = parts[0].split("://")[1].strip()
    key = domain_and_key[1].strip()
    return bucket, key


async def download_file_from_s3(url):
    bucket, key = await parse_s3_url(url)
    file_buffer = BytesIO()
    s3.download_fileobj(bucket, key, file_buffer)
    file_buffer.seek(0)
    return file_buffer


async def encode_file_to_base64(file_buffer):
    return base64.b64encode(file_buffer.read()).decode()
