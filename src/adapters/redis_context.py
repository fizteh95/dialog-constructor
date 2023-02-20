import json
import typing as tp

import redis.asyncio as redis

from src import settings
from src.adapters.repository import AbstractContextRepo
from src.domain.model import User


class RedisContextRepo(AbstractContextRepo):
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str]
    ) -> None:
        """Update user fields"""
        unparsed_ctx: str | None = await self.redis.get(user.outer_id)
        if unparsed_ctx is None:
            exists_ctx = {}
        else:
            exists_ctx = json.loads(unparsed_ctx)
        new_context = exists_ctx | ctx_to_update
        await self.redis.set(user.outer_id, json.dumps(new_context))

    async def clear_user_context(
        self,
        user: User,
    ) -> None:
        """Clear user context (only loop counters)"""
        unparsed_ctx: str | None = await self.redis.get(user.outer_id)
        if unparsed_ctx is None:
            exists_ctx = {}
        else:
            exists_ctx = json.loads(unparsed_ctx)
        new_context = {}
        for k in list(exists_ctx.keys()):
            if "_loopCount" in k:
                continue
            new_context[k] = exists_ctx[k]
        await self.redis.set(user.outer_id, json.dumps(new_context))

    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""
        unparsed_ctx: str | None = await self.redis.get(user.outer_id)
        if unparsed_ctx is None:
            return {}
        exists_ctx: tp.Dict[str, str] = json.loads(unparsed_ctx)
        return exists_ctx
