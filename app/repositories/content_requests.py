"""Content request repository."""

from typing import Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content_request import ContentRequest
from app.constants.enums import ContentRequestStatus


class ContentRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, req: ContentRequest) -> ContentRequest:
        self.db.add(req)
        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def get_by_id(self, req_id: str) -> Optional[ContentRequest]:
        result = await self.db.execute(
            select(ContentRequest).where(ContentRequest.id == req_id)
        )
        return result.scalar_one_or_none()

    async def list_incoming(
        self, owner_id: str, status: Optional[ContentRequestStatus] = None
    ) -> list[ContentRequest]:
        """Requests on entities owned by owner_id."""
        q = select(ContentRequest).where(ContentRequest.entity_owner_id == owner_id)
        if status:
            q = q.where(ContentRequest.status == status)
        q = q.order_by(ContentRequest.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_outgoing(
        self, requester_id: str, status: Optional[ContentRequestStatus] = None
    ) -> list[ContentRequest]:
        q = select(ContentRequest).where(ContentRequest.requester_id == requester_id)
        if status:
            q = q.where(ContentRequest.status == status)
        q = q.order_by(ContentRequest.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def count_incoming_pending(self, owner_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                ContentRequest.entity_owner_id == owner_id,
                ContentRequest.status == ContentRequestStatus.PENDING,
            )
        )
        return result.scalar_one()

    async def review(
        self,
        req_id: str,
        reviewer_id: str,
        status: ContentRequestStatus,
        note: Optional[str],
    ) -> Optional[ContentRequest]:
        await self.db.execute(
            update(ContentRequest)
            .where(ContentRequest.id == req_id)
            .values(status=status, reviewer_id=reviewer_id, reviewer_note=note)
        )
        await self.db.flush()
        return await self.get_by_id(req_id)
