from datetime import UTC
import datetime
from http.client import HTTPException
import json
import json
import os
import secrets
from app.core.redis_manager import redis_manager
from app.core.passkey.passkey_manager import passkey_manager
from app.config import settings
from app.core.encoding import b64url_encode
import base64
from app.config import WEBAUTHN_USER_HANDLE_BYTES
from sqlmodel import select
from app.models.user import User
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy.orm import selectinload

from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

from app.schemas.auth import AuthenticationBeginRequest, AuthenticationCompleteRequest, RegistrationCompleteRequest
from app.models.credential import Credential

logger = logging.getLogger(__name__)

async def get_user_by_username(
    self,
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()

class AuthService:
    async def register_begin(self, session, username: str, display_name: str):
        result = await session.execute(
            select(User).where(User.username == username)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User already exists")

        from app.config import WEBAUTHN_USER_HANDLE_BYTES
        user_handle = secrets.token_bytes(WEBAUTHN_USER_HANDLE_BYTES)

        options_response = passkey_manager.generate_registration_options(
            user_id = user_handle,
            username = username,
            display_name = display_name,
            exclude_credentials = [],
        )

        await redis_manager.set_registration_context(
            username = username,
            challenge = options_response.challenge,
            user_handle = user_handle,
            display_name = display_name,
        )

        logger.info("Started registration for user: %s", username)
        return options_response.options

    async def complete_registration(self, session: AsyncSession, body: RegistrationCompleteRequest):
        result = await session.execute(
            select(User)
            .options(selectinload(User.credentials))
            .where(User.username == body.username)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User already exists")

        context = await redis_manager.get_and_delete_registration_context(body.username)

        if not context:
            raise ValueError("Registration context not found or expired")

        expected_challenge = base64.b64decode(context["challenge"])

        verified = passkey_manager.verify_registration_response(
            response=body.credential,
            expected_challenge=expected_challenge,
        )

        user = User(
            username=body.username,
            display_name=context["display_name"],
            webauthn_user_handle=base64.b64decode(context["user_handle"]),
        )

        session.add(user)
        await session.flush()

        backup_eligible = getattr(verified, "backup_eligible", False)
        backup_state = getattr(verified, "backup_state", False)

        credential = Credential(
            user_id=user.id,

            credential_id=bytes_to_base64url(verified.credential_id),
            public_key=bytes_to_base64url(verified.credential_public_key),

            sign_count=verified.sign_count,
            aaguid=bytes_to_base64url(verified.aaguid),

            backup_eligible=backup_eligible,
            backup_state=backup_state,

            attestation_type=verified.attestation_format,

            device_name="Passkey",
            last_used_at=datetime.datetime.now(datetime.timezone.utc),
        )

        session.add(credential)

        await session.commit()
        await session.refresh(user)

        # STORE CREDENTIAL


        logger.info("Completed registration for user: %s", body.username)
        return user

    async def begin_authentication(self, session: AsyncSession, body: AuthenticationBeginRequest):
        result = await session.execute(
            select(User)
            .options(selectinload(User.credentials))
            .where(User.username == body.username)
        )

        existing_user = result.scalar_one_or_none()

        if not existing_user:
            raise ValueError("User not found")
            
        if existing_user is not None and existing_user.is_active:
                allow_credentials = [
                    base64url_to_bytes(cred.credential_id)
                    for cred in existing_user.credentials
                ]
        else:
            allow_credentials = []       
        
        options_response = passkey_manager.generate_authentication_options(
            user_handle=existing_user.webauthn_user_handle,
            allowed_credentials=allow_credentials,
        )

        await redis_manager.set_authentication_challenge(
            challenge = options_response.challenge,
        )

        logger.info(
            "Started authentication (username hint: %s)",
            body.username or "<discoverable>"
        )
        return options_response.options
    
    async def complete_authentication(self, session: AsyncSession, body: AuthenticationCompleteRequest):
        credential_id = body.credential.get("id")
        if not credential_id:
            raise ValueError("Missing credential ID")

        client_data_b64 = body.credential.get("response", {}).get(
            "clientDataJSON"
        )
        if not client_data_b64:
            raise ValueError("Missing clientDataJSON")

        try:
            client_data = json.loads(
                base64url_to_bytes(client_data_b64).decode()
            )
            challenge_bytes = base64url_to_bytes(client_data["challenge"])
        except Exception as exc:
            logger.error("Failed to parse clientDataJSON: %s", exc)
            raise ValueError("Malformed clientDataJSON") from exc

        challenge_consumed = await redis_manager.take_authentication_challenge(
            challenge = challenge_bytes
        )
        if not challenge_consumed:
            logger.warning(
                "Authentication challenge invalid or expired"
            )
            raise ValueError(
                "Challenge expired or not found - please restart authentication"
            )
        
        result = await session.execute(
            select(Credential).where(Credential.credential_id == credential_id)
        )
        credential = result.scalar_one_or_none()

        if not credential:
            logger.warning(
                "Authentication with unknown credential: %s...",
                credential_id[: 16]
            )
            raise ValueError("Credential not found")
        
        result = await session.execute(
            select(User).where(User.id == credential.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(
                "User not found for credential: %s...",
                credential_id[: 16]
            )
            raise ValueError("User not found")

        if not user.is_active:
            logger.warning(
                "Authentication attempt for inactive user: %s",
                user.username
            )
            raise ValueError("User account is inactive")

        try:
            verified = passkey_manager.verify_authentication(
                credential = body.credential,
                expected_challenge = challenge_bytes,
                credential_public_key = base64url_to_bytes(credential.public_key),
                credential_current_sign_count = credential.sign_count,
            )
        except ValueError as e:
            logger.error("Authentication verification failed: %s", e)
            raise ValueError(str(e)) from e
        except Exception as e:
            logger.error("Unexpected error during authentication: %s", e)
            raise ValueError(
                "Authentication verification failed"
            ) from e

        credential.sign_count = verified.new_sign_count
        credential.last_used_at = datetime.datetime.now(datetime.timezone.utc)

        new_backup_eligible = getattr(verified, "backup_eligible", False)
        new_backup_state = getattr(verified, "backup_state", False)

        if ( credential.backup_state != new_backup_state or credential.backup_eligible != new_backup_eligible ):
            credential.backup_state = new_backup_state
            credential.backup_eligible = new_backup_eligible

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database error updating credential: %s", e)
            raise ValueError("Failed to update credential state") from e

        logger.info("Authentication successful for user: %s", user.username)
        return user



auth_service = AuthService()