"""Friend request repository — data access for FriendRequest model."""

from typing import Optional
from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.friend_request import FriendRequest
from app.constants.enums import FriendRequestStatus


class FriendRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, request: FriendRequest) -> FriendRequest:
        self.db.add(request)
        await self.db.flush()
        await self.db.refresh(request)
        return request

    async def get_by_id(self, request_id: str) -> Optional[FriendRequest]:
        result = await self.db.execute(
            select(FriendRequest).where(FriendRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_between(self, user_a: str, user_b: str) -> Optional[FriendRequest]:
        """Return any request between the two users (in either direction)."""
        result = await self.db.execute(
            select(FriendRequest).where(
                or_(
                    and_(
                        FriendRequest.sender_id == user_a,
                        FriendRequest.receiver_id == user_b,
                    ),
                    and_(
                        FriendRequest.sender_id == user_b,
                        FriendRequest.receiver_id == user_a,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_incoming(self, user_id: str) -> list[FriendRequest]:
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.receiver_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
        )
        return list(result.scalars().all())

    async def list_outgoing(self, user_id: str) -> list[FriendRequest]:
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.sender_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
        )
        return list(result.scalars().all())

    async def list_friends(self, user_id: str) -> list[FriendRequest]:
        """Return all accepted friendships involving user_id."""
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.status == FriendRequestStatus.ACCEPTED,
                or_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.receiver_id == user_id,
                ),
            )
        )
        return list(result.scalars().all())

    async def update_status(
        self, request_id: str, status: FriendRequestStatus
    ) -> Optional[FriendRequest]:
        await self.db.execute(
            update(FriendRequest)
            .where(FriendRequest.id == request_id)
            .values(status=status)
        )
        await self.db.flush()
        return await self.get_by_id(request_id)

    async def are_friends(self, user_a: str, user_b: str) -> bool:
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.status == FriendRequestStatus.ACCEPTED,
                or_(
                    and_(
                        FriendRequest.sender_id == user_a,
                        FriendRequest.receiver_id == user_b,
                    ),
                    and_(
                        FriendRequest.sender_id == user_b,
                        FriendRequest.receiver_id == user_a,
                    ),
                ),
            )
        )
        return result.scalar_one_or_none() is not None
