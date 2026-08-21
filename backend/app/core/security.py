"""
LEDGER — Security Utilities
JWT generation/validation, password hashing, RBAC dependencies.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

import bcrypt

# OAuth2 token scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))


def create_access_token(
    subject: str,
    role: str,
    user_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Issue a signed JWT with role claim."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "role": role,
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "ledger-credit-intelligence",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


class CurrentUser:
    """Resolved from JWT token — attached to request state."""
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "demo_admin"

    @property
    def is_underwriter(self) -> bool:
        return self.role in ("underwriter", "demo_admin")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> CurrentUser:
    """FastAPI dependency — validate JWT and return current user."""
    payload = decode_token(token)
    user_id = payload.get("user_id")
    email = payload.get("sub")
    role = payload.get("role")
    if not user_id or not email or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    return CurrentUser(user_id=user_id, email=email, role=role)


async def require_underwriter(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """RBAC: require underwriter or admin role."""
    if not current_user.is_underwriter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Underwriter role required",
        )
    return current_user


async def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """RBAC: require demo_admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user
