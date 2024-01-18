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
    if "iat" in data.keys():
        data['iat'] = data['iat'].isoformat() if 'iat' in data else None
    json_str = json.dumps(data, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    json_str = lzma.compress(json_bytes)
    cipher_text = cipher_suite.encrypt(json_str)
    encrypted_str = base64.urlsafe_b64encode(cipher_text).decode()
    return encrypted_str

async def decrypt(key:str)->dict:
    try:
        padding = len(key) % 4
        if padding != 0:
            key += '=' * (4 - padding)
        decoded_text = base64.urlsafe_b64decode(key.encode())
        decrypted_text = cipher_suite.decrypt(decoded_text)
        decompressed_data = lzma.decompress(decrypted_text)
        decoded_dict = json.loads(decompressed_data.decode('utf-8'))
        if "iat" in decoded_dict.keys():
            decoded_dict['iat'] = datetime.datetime.strptime(decoded_dict['iat'], '%Y-%m-%dT%H:%M:%S.%f') if 'iat' in decoded_dict else None
        return decoded_dict
    except InvalidToken as e:
        traceback.print_exc()
        logger.error(f"InvalidToken exception during decryption: {e}")
        return {}
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        return{}