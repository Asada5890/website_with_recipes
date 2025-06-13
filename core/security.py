from passlib.context import CryptContext
from jose import jwt
from typing import Optional
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel
from .settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)





oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class TokenData(BaseModel):
    email: Optional[str] = None

    
async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    
    print(f"[DEBUG] Token from cookies: {token}")  # Логирование
    
    if not token:
        return None
    
    try:
        # Удаление Bearer даже если его нет
        clean_token = token.replace("Bearer ", "").strip()
        payload = jwt.decode(
            clean_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        print(f"[DEBUG] Decoded payload: {payload}")  # Логирование
        return payload
    except Exception as e:
        print(f"[ERROR] Token decode failed: {str(e)}")
        return None