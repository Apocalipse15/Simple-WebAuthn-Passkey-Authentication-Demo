import logging
import secrets
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

from app.core.redis_manager import redis_manager
from app.models.user import User
from app.services.auth_service import auth_service
from app.db import get_session


logger = logging.getLogger(__name__)

async def issue_session(response: Response, user: User) -> str:
    """
    Create a session token, persist it in Redis, and attach the cookie
    """
    token = secrets.token_urlsafe(settings.SESSION_TOKEN_BYTES)
    await redis_manager.create_session(
        token = token,
        user_id = str(user.id),
        ttl = settings.SESSION_TTL_SECONDS,
    )
    response.set_cookie(
        key = settings.SESSION_COOKIE_NAME,
        value = token,
        max_age = settings.SESSION_TTL_SECONDS,
        httponly = True,
        secure = False, # Change to work with .env
        samesite = "lax",
        path = "/",
    )
    return token

async def current_user(chat_session: str | None = Cookie(default = None, alias = settings.SESSION_COOKIE_NAME),
    session: AsyncSession = Depends(get_session)):
    logger.info("Attempting to retrieve current user from session cookie")
    if not chat_session:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Not authenticated")
    
    user_id = await redis_manager.get_session(chat_session)
    if not user_id:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Session expired or invalid")
    
    user = await session.get(User, UUID(user_id["user_id"]))
    if not user or not user.is_active:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "User not found")
    return user
