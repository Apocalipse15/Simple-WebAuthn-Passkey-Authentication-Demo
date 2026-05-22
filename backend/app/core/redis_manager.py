import base64

import redis.asyncio as redis
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=False)

    async def set_challenge(self, key: str, value: bytes, ttl: int):
        await self.client.setex(key, ttl, value)

    async def get_and_delete_challenge(self, key: str):
        pipe = self.client.pipeline()
        pipe.get(key)
        pipe.delete(key)
        result = await pipe.execute()
        return result[0]

    async def set_registration_context(self, username, challenge, user_handle, display_name):
        value = json.dumps({
            "challenge": base64.b64encode(challenge).decode("utf-8"),
            "user_handle": base64.b64encode(user_handle).decode("utf-8"),
            "display_name": display_name,
        })

        await self.client.setex(
            f"webauthn:register:{username}",
            settings.WEBAUTHN_CHALLENGE_TTL_SECONDS,
            value
        )

    async def get_and_delete_registration_context(self, username: str):
        key = f"webauthn:register:{username}"

        pipe = self.client.pipeline()
        pipe.get(key)
        pipe.delete(key)

        result = await pipe.execute()
        logger.debug("Retrieved and deleted registration context for user %s from Redis", username)
        data = result[0]

        if not data:
            return None

        return json.loads(data.decode("utf-8"))

    async def create_session(self, token: str, user_id: str, ttl: int):
        key = f"session:{token}"
        value = json.dumps({"user_id": user_id})
        await self.client.setex(key, ttl, value)

    async def get_session(self, token: str):
        key = f"session:{token}"
        data = await self.client.get(key)
        if not data:
            return None
        return json.loads(data.decode("utf-8"))
    
    async def set_authentication_challenge(self, challenge: bytes, ttl: int = settings.WEBAUTHN_CHALLENGE_TTL_SECONDS):
        key = f"webauthn:auth:{challenge}"
        await self.client.setex(key, ttl, challenge)

    async def take_authentication_challenge(self, challenge: str):
        key = f"webauthn:auth:{challenge}"
        result = await self.client.delete(key)
        return result == 1
    

redis_manager = RedisManager()