"""Friend service — business logic for the friend / social system."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.friends import FriendRequestRepository
from app.models.friend_request import FriendRequest
from app.models.user import User
from app.schemas.friends import (
    FriendRequestResponse,
    FriendResponse,
    UserSearchResult,
)
from app.constants.enums import FriendRequestStatus
from app.exceptions.friends import (
    FriendRequestNotFoundException,
    AlreadyFriendsException,
    FriendRequestAlreadySentException,
    CannotFriendSelfException,
    FriendRequestForbiddenException,
)
from app.exceptions.auth import UserNotFoundException


class FriendService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FriendRequestRepository(db)

    async def _get_user(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundException()
        return user

    def _to_request_response(
        self, req: FriendRequest, sender: User
    ) -> FriendRequestResponse:
        return FriendRequestResponse(
            id=req.id,
            sender_id=req.sender_id,
            receiver_id=req.receiver_id,
            sender_username=sender.username,
            sender_avatar=sender.avatar_url,
            status=FriendRequestStatus(req.status),
            created_at=req.created_at,
        )

    # ── Search ────────────────────────────────────────────────────────────────

    async def search_users(
        self, query: str, current_user_id: str
    ) -> list[UserSearchResult]:
        result = await self.db.execute(
            select(User).where(
                User.username.ilike(f"%{query}%"),
                User.id != current_user_id,
            ).limit(20)
        )
        users = result.scalars().all()

        friends_set: set[str] = set()
        pending_map: dict[str, str] = {}

        for u in users:
            req = await self.repo.get_between(current_user_id, u.id)
            if req:
                if req.status == FriendRequestStatus.ACCEPTED:
                    friends_set.add(u.id)
                elif req.status == FriendRequestStatus.PENDING:
                    pending_map[u.id] = req.id

        return [
            UserSearchResult(
                id=u.id,
                username=u.username,
                full_name=u.full_name,
                avatar_url=u.avatar_url,
                is_friend=u.id in friends_set,
                pending_request_id=pending_map.get(u.id),
            )
            for u in users
        ]

    # ── Send request ─────────────────────────────────────────────────────────

    async def send_request(
        self, sender_id: str, receiver_id: str
    ) -> FriendRequestResponse:
        if sender_id == receiver_id:
            raise CannotFriendSelfException()

        await self._get_user(receiver_id)

        existing = await self.repo.get_between(sender_id, receiver_id)
        if existing:
            if existing.status == FriendRequestStatus.ACCEPTED:
                raise AlreadyFriendsException()
            if existing.status == FriendRequestStatus.PENDING:
                raise FriendRequestAlreadySentException()
            # REJECTED or CANCELLED — allow re-sending by updating status
            updated = await self.repo.update_status(
                existing.id, FriendRequestStatus.PENDING
            )
            sender = await self._get_user(sender_id)
            return self._to_request_response(updated, sender)  # type: ignore

        req = FriendRequest(
            sender_id=sender_id,
            receiver_id=receiver_id,
        )
        created = await self.repo.create(req)
        sender = await self._get_user(sender_id)
        return self._to_request_response(created, sender)

    # ── Respond to request ───────────────────────────────────────────────────

    async def accept_request(
        self, request_id: str, current_user_id: str
    ) -> FriendRequestResponse:
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise FriendRequestNotFoundException()
        if req.receiver_id != current_user_id:
            raise FriendRequestForbiddenException()
        updated = await self.repo.update_status(
            request_id, FriendRequestStatus.ACCEPTED
        )
        sender = await self._get_user(updated.sender_id)  # type: ignore
        return self._to_request_response(updated, sender)  # type: ignore

    async def reject_request(
        self, request_id: str, current_user_id: str
    ) -> FriendRequestResponse:
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise FriendRequestNotFoundException()
        if req.receiver_id != current_user_id:
            raise FriendRequestForbiddenException()
        updated = await self.repo.update_status(
            request_id, FriendRequestStatus.REJECTED
        )
        sender = await self._get_user(updated.sender_id)  # type: ignore
        return self._to_request_response(updated, sender)  # type: ignore

    async def cancel_request(
        self, request_id: str, current_user_id: str
    ) -> None:
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise FriendRequestNotFoundException()
        if req.sender_id != current_user_id:
            raise FriendRequestForbiddenException()
        await self.repo.update_status(request_id, FriendRequestStatus.CANCELLED)

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_incoming_requests(
        self, user_id: str
    ) -> list[FriendRequestResponse]:
        requests = await self.repo.list_incoming(user_id)
        result = []
        for req in requests:
            sender = await self._get_user(req.sender_id)
            result.append(self._to_request_response(req, sender))
        return result

    async def list_outgoing_requests(
        self, user_id: str
    ) -> list[FriendRequestResponse]:
        requests = await self.repo.list_outgoing(user_id)
        result = []
        for req in requests:
            sender = await self._get_user(req.sender_id)
            response = self._to_request_response(req, sender)
            receiver = await self._get_user(req.receiver_id)
            response.receiver_username = receiver.username
            result.append(response)
        return result

    async def list_friends(self, user_id: str) -> list[FriendResponse]:
        friendships = await self.repo.list_friends(user_id)
        result = []
        for fs in friendships:
            friend_id = (
                fs.receiver_id if fs.sender_id == user_id else fs.sender_id
            )
            friend = await self._get_user(friend_id)
            result.append(
                FriendResponse(
                    id=friend.id,
                    username=friend.username,
                    full_name=friend.full_name,
                    avatar_url=friend.avatar_url,
                    bio=friend.bio,
                )
            )
        return result

    async def unfriend(self, user_id: str, friend_id: str) -> None:
        req = await self.repo.get_between(user_id, friend_id)
        if not req or req.status != FriendRequestStatus.ACCEPTED:
            raise FriendRequestNotFoundException()
        await self.repo.update_status(req.id, FriendRequestStatus.CANCELLED)
