"""Authentication endpoints with revocable opaque bearer sessions."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.models import Organization, Session, User
from app.security import new_session_token, token_digest, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
AuthorizationHeader = Annotated[str | None, Header()]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class SessionResponse(BaseModel):
    token: str
    expires_at: datetime
    user: dict[str, str]


async def current_user(
    db: DatabaseSession,
    authorization: AuthorizationHeader = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    digest = token_digest(authorization.removeprefix("Bearer "))
    query = (
        select(User)
        .join(Session, Session.user_id == User.id)
        .where(Session.token_hash == digest, Session.expires_at > datetime.now(UTC))
    )
    user = await db.scalar(query)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session is invalid or expired")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest, db: DatabaseSession) -> SessionResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token, digest = new_session_token()
    expires = datetime.now(UTC) + timedelta(hours=get_settings().session_hours)
    db.add(Session(user_id=user.id, token_hash=digest, expires_at=expires))
    await db.commit()
    return SessionResponse(
        token=token,
        expires_at=expires,
        user={"email": user.email, "display_name": user.display_name, "role": user.role},
    )


@router.get("/me")
async def me(user: CurrentUser, db: DatabaseSession) -> dict[str, str]:
    organization = await db.get(Organization, user.organization_id)
    return {
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "organization": organization.name if organization else "Unknown",
    }


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    _: CurrentUser,
    db: DatabaseSession,
    authorization: AuthorizationHeader = None,
) -> None:
    if authorization:
        await db.execute(
            delete(Session).where(Session.token_hash == token_digest(authorization[7:]))
        )
        await db.commit()
