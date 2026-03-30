"""Permission repository — data access for Permission model with Redis caching."""

import json
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.permission import Permission
from app.constants.enums import EntityType
from app.utils.redis import redis_client

PERM_CACHE_TTL = 300  # 5 minutes


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_permission(
        self, user_id: str, entity_type: EntityType, entity_id: str
    ) -> Optional[Permission]:
        cache_key = f"perm:{user_id}:{entity_type.value}:{entity_id}"
        try:
            cached = await redis_client.get(cache_key)
            if cached is not None:
                if cached == "null":
                    return None
                data = json.loads(cached)
                return Permission(**data)
        except Exception:
            pass

        result = await self.db.execute(
            select(Permission).where(
                Permission.user_id == user_id,
                Permission.entity_type == entity_type,
                Permission.entity_id == entity_id,
            )
        )
        perm = result.scalar_one_or_none()

        try:
            if perm:
                cache_data = {
                    "id": perm.id,
                    "user_id": perm.user_id,
                    "entity_type": perm.entity_type.value
                    if hasattr(perm.entity_type, "value")
                    else perm.entity_type,
                    "entity_id": perm.entity_id,
                    "role": perm.role.value
                    if hasattr(perm.role, "value")
                    else perm.role,
                    "granted_by": perm.granted_by,
                }
                await redis_client.setex(
                    cache_key, PERM_CACHE_TTL, json.dumps(cache_data)
                )
            else:
                await redis_client.setex(cache_key, PERM_CACHE_TTL, "null")
        except Exception:
            pass

        return perm

    async def grant(self, permission: Permission) -> Permission:
        self.db.add(permission)
        await self.db.flush()
        await self._invalidate_cache(
            permission.user_id, permission.entity_type, permission.entity_id
        )
        return permission

    async def revoke(
        self, user_id: str, entity_type: EntityType, entity_id: str
    ) -> None:
        await self.db.execute(
            delete(Permission).where(
                Permission.user_id == user_id,
                Permission.entity_type == entity_type,
                Permission.entity_id == entity_id,
            )
        )
        await self.db.flush()
        await self._invalidate_cache(user_id, entity_type, entity_id)

    async def list_by_entity(
        self, entity_type: EntityType, entity_id: str
    ) -> list[Permission]:
        result = await self.db.execute(
            select(Permission).where(
                Permission.entity_type == entity_type,
                Permission.entity_id == entity_id,
            )
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: str) -> list[Permission]:
        result = await self.db.execute(
            select(Permission).where(Permission.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _invalidate_cache(
        self, user_id: str, entity_type, entity_id: str
    ) -> None:
        et = (
            entity_type.value
            if hasattr(entity_type, "value")
            else entity_type
        )
        cache_key = f"perm:{user_id}:{et}:{entity_id}"
        try:
            await redis_client.delete(cache_key)
        except Exception:
            pass
