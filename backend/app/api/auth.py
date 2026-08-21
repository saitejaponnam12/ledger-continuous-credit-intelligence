"""LEDGER — Auth Router"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.models import User

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: str
    role: str
    expires_in_minutes: int = 60


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Issue JWT token. Credentials validated against hashed passwords."""
    result = await db.execute(
        select(User).where(User.email == form_data.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    print(f"[AUTH DEBUG] email={form_data.username}, user_found={user is not None}")
    if user:
        pwd_ok = verify_password(form_data.password, user.hashed_password)
        print(f"[AUTH DEBUG] password_match={pwd_ok}, hash={user.hashed_password[:20]}")

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    await db.execute(
        update(User).where(User.id == user.id).values(last_login=datetime.now(timezone.utc))
    )

    token = create_access_token(
        subject=user.email,
        role=user.role,
        user_id=str(user.id),
    )

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
        role=user.role,
    )


class MeResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str


@router.get("/me", response_model=MeResponse)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(__import__("app.core.security", fromlist=["get_current_user"]).get_current_user),
):
    """Return the currently authenticated user's profile."""
    result = await db.execute(select(User).where(User.email == current_user.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return MeResponse(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )
