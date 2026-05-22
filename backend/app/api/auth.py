from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.schemas.auth import AuthenticationBeginRequest, AuthenticationCompleteRequest, RegistrationBeginRequest, RegistrationCompleteRequest
from app.services.auth_service import auth_service
import logging

from app.core.encoding import b64url_encode
from app.schemas.user import UserRead

from app.core.dependencies import (
    current_user,
    issue_session,
    #revoke_session,
    #session_token_from_cookie,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/begin")
async def register_begin(
    body: RegistrationBeginRequest,
    session: AsyncSession = Depends(get_session),
):
    logger.info("Received registration begin request for username: %s", body.username)
    print("REGISTER BEGIN USERNAME: %s\n\n", body.username)

    aux = await auth_service.register_begin(
        session,
        body.username,
        body.display_name
    )
    logger.info("Options generated for user %s: %s", body.username, aux)
    return aux

@router.post("/register/complete", status_code=201)
async def register_complete(request: Request,
    body: RegistrationCompleteRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),):
    print("COMPLETE USERNAME:\n\n", body.username)
    user = await auth_service.complete_registration(session, body)
    await issue_session(response, user)
    return UserRead.model_validate(user)



@router.post("/authenticate/begin")
async def authenticate_begin(request: Request,
    body: AuthenticationBeginRequest,
    session: AsyncSession = Depends(get_session),):
    logger.info("Received authentication begin request")
    return await auth_service.begin_authentication(session, body)



@router.post("/authenticate/complete")
async def authenticate_complete(
    request: Request,
    body: AuthenticationCompleteRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),):
    user = await auth_service.complete_authentication(session, body)
    await issue_session(response, user)
    return UserRead.model_validate(user)

# Endpoints for session management

@router.get("/me", status_code = 200)
async def me(user: User = Depends(current_user)):
    """
    Return the user bound to the current session
    """
    logger.info("Received request for current user info: %s", user.username)
    return UserRead.model_validate(user)

"""

@router.post("/logout", status_code = 204)
async def logout(
    response: Response,
    token: str | None = Depends(session_token_from_cookie),
) -> None:
    await revoke_session(response, token)


@router.post("/users/search", status_code = 200)
async def search_users(
    request: Request,
    body: UserSearchRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> UserSearchResponse:
       
    users = await auth_service.search_users(
        session,
        body.query,
        body.limit,
        exclude_user_id = user.id,
    )

    return UserSearchResponse(
        users = [UserRead.model_validate(u) for u in users]
    ) 
"""