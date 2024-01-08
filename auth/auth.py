from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
import datetime

from starlette import status

from repos.admin_repos import find_admin_filtered


class AuthHandler:
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=['bcrypt'])
    secret = 'supersecret'
    candidate_revoked_tokens = set()
    admin_revoked_tokens = set()
    
    async def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload['id']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Expired Signature')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid Token')

    async def get_current_admin(self, auth: HTTPAuthorizationCredentials = Security(security)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials'
        )
        username = await self.decode_token(auth.credentials)
        if username is None:
            raise credentials_exception
        admin = await find_admin_filtered(username)
        if admin is None:
            raise credentials_exception
        return admin