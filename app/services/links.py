"""Shared link service."""

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.links import SharedLinkRepository
from app.models.shared_link import SharedLink
from app.schemas.links import GenerateLinkRequest, SharedLinkResponse, ResolvedLinkResponse
from app.constants.enums import LinkTargetType
from app.exceptions.links import SharedLinkNotFoundException


class SharedLinkService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SharedLinkRepository(db)

    def _to_response(self, link: SharedLink) -> SharedLinkResponse:
        return SharedLinkResponse(
            id=link.id,
            short_code=link.short_code,
            target_type=LinkTargetType(link.target_type),
            target_id=link.target_id,
            creator_id=link.creator_id,
            expires_at=link.expires_at,
            is_active=link.is_active,
            created_at=link.created_at,
        )

    async def generate(
        self, creator_id: str, data: GenerateLinkRequest
    ) -> SharedLinkResponse:
        link = SharedLink(
            target_type=data.target_type.value,
            target_id=data.target_id,
            creator_id=creator_id,
            expires_at=data.expires_at,
        )
        created = await self.repo.create(link)
        return self._to_response(created)

    async def resolve(self, short_code: str) -> ResolvedLinkResponse:
        link = await self.repo.get_by_code(short_code)
        if not link or not link.is_active:
            raise SharedLinkNotFoundException()
        if link.expires_at and link.expires_at < datetime.now(timezone.utc):
            raise SharedLinkNotFoundException()

        # Return minimal resolved data; callers use the target_id with existing APIs
        resolved: dict[str, Any] = {
            "target_type": link.target_type,
            "target_id": link.target_id,
        }
        return ResolvedLinkResponse(link=self._to_response(link), data=resolved)

    async def list_my_links(self, user_id: str) -> list[SharedLinkResponse]:
        links = await self.repo.list_by_creator(user_id)
        return [self._to_response(l) for l in links]
