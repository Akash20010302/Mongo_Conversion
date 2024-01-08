import datetime
from cryptography.fernet import Fernet,InvalidToken
import base64
import json
import traceback
import lzma
from loguru import logger


key=b'j5YFcJldLdm4ZRWq8eLkDR5nKx5j3rIb638HSIEd0bM='
cipher_suite = Fernet(key)

async def encrypt(data:dict)->str:
    json_str = json.dumps(data)
    json_str = lzma.compress(json_str.encode())
    cipher_text = cipher_suite.encrypt(json_str)
    encrypted_str = base64.urlsafe_b64encode(cipher_text).decode()
    return encrypted_str

async def decrypt(key:str)->dict:
    try:
        decoded_text = base64.urlsafe_b64decode(key.encode())
        decrypted_text = cipher_suite.decrypt(decoded_text)
        decrypted_text = lzma.decompress(decrypted_text)
        decoded_dict = json.loads(decrypted_text.decode())
        return decoded_dict
    except InvalidToken as e:
        traceback.print_exc()
        logger.error(f"InvalidToken exception during decryption: {e}")
        return {}
    except Exception as e:
        logger.error(e)
        return{}