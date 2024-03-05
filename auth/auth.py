from fastapi import Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
import datetime
from sqlmodel import Session
from starlette import status
from db.db import get_db_backend

from repos.admin_repos import find_admin_filtered


class AuthHandler:
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"])
    secret = "supersecret"
    session_key = "qctriopmlcaxzryhkloyvcdalfrtsghdcets"
    candidate_revoked_tokens = set()
    admin_revoked_tokens = set()

    async def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    async def verify_password(self, pwd, hashed_pwd):
        return self.pwd_context.verify(pwd, hashed_pwd)

    async def encode_token(self, user_id, role):
        payload = {
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            "iat": datetime.datetime.utcnow(),
            "id": user_id,
            "role": role,
        }
        return jwt.encode(payload, self.session_key, algorithm="HS256")

    async def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.session_key, algorithms=["HS256"])
            return payload["id"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Expired Signature")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid Token")

    async def auth_wrapper(
        self, auth: HTTPAuthorizationCredentials = Security(security)
    ):
        return await self.decode_token(auth.credentials)

    async def get_current_admin(
        self,
        auth: HTTPAuthorizationCredentials = Security(security),
        session: Session = Depends(get_db_backend),
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        expired_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired Signature",
        )
        if auth.credentials not in self.admin_revoked_tokens:
            username = await self.decode_token(auth.credentials)
            if username is None:
                raise credentials_exception
            admin = find_admin_filtered(email=username, session=session)
            if admin is None:
                raise credentials_exception
            return admin
        else:
            raise expired_exception

    async def decode_token_role(self, token):
        try:
            payload = jwt.decode(token, self.session_key, algorithms=["HS256"])
            return payload["role"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Expired Signature")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid Token")

