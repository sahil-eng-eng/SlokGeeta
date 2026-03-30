"""Friend system routes.

POST   /friends/request              — send a friend request
GET    /friends/requests/incoming    — list incoming pending requests
GET    /friends/requests/outgoing    — list outgoing pending requests
PATCH  /friends/requests/{id}/accept — accept a request
PATCH  /friends/requests/{id}/reject — reject a request
DELETE /friends/requests/{id}        — cancel own request
GET    /friends                      — list accepted friends
DELETE /friends/{friend_id}          — unfriend
GET    /users/search?q=              — search users
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.services.friends import FriendService
from app.schemas.friends import (
    SendFriendRequestRequest,
    FriendRequestResponse,
    FriendResponse,
    UserSearchResult,
)
from app.core.responses import ApiResponse
from app.constants.messages import FRIEND_MESSAGES

router = APIRouter(tags=["friends"])


def _get_service(db: AsyncSession = Depends(get_db)) -> FriendService:
    return FriendService(db)


@router.get("/users/search", response_model=None)
async def search_users(
    q: str = Query(min_length=2),
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    results = await service.search_users(q, current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=FRIEND_MESSAGES["SEARCH_RETRIEVED"],
    )


@router.post("/friends/request", status_code=201, response_model=None)
async def send_friend_request(
    body: SendFriendRequestRequest,
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    result = await service.send_request(current_user.id, body.receiver_id)
    # Real-time: notify the receiver that they have a new friend request
    await ws_manager.send_to_user(
        body.receiver_id,
        {"type": "friend_request", "data": result.model_dump(mode="json")},
    )
    return ApiResponse(status_code=201, data=result.model_dump(), message=FRIEND_MESSAGES["REQUEST_SENT"])


@router.get("/friends/requests/incoming", response_model=None)
async def list_incoming_requests(
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    results = await service.list_incoming_requests(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=FRIEND_MESSAGES["FRIENDS_RETRIEVED"],
    )


@router.get("/friends/requests/outgoing", response_model=None)
async def list_outgoing_requests(
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    results = await service.list_outgoing_requests(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=FRIEND_MESSAGES["FRIENDS_RETRIEVED"],
    )


@router.patch("/friends/requests/{request_id}/accept", response_model=None)
async def accept_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    result = await service.accept_request(request_id, current_user.id)
    # Real-time: notify the original sender that their request was accepted
    await ws_manager.send_to_user(
        result.sender_id,
        {"type": "friend_accepted", "data": result.model_dump(mode="json")},
    )
    return ApiResponse(status_code=200, data=result.model_dump(), message=FRIEND_MESSAGES["REQUEST_ACCEPTED"])


@router.patch("/friends/requests/{request_id}/reject", response_model=None)
async def reject_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    result = await service.reject_request(request_id, current_user.id)
    # Real-time: notify the original sender that their request was rejected
    await ws_manager.send_to_user(
        result.sender_id,
        {"type": "friend_rejected", "data": {"request_id": result.id}},
    )
    return ApiResponse(status_code=200, data=result.model_dump(), message=FRIEND_MESSAGES["REQUEST_REJECTED"])


@router.delete("/friends/requests/{request_id}", status_code=204)
async def cancel_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    await service.cancel_request(request_id, current_user.id)


@router.get("/friends", response_model=None)
async def list_friends(
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    results = await service.list_friends(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=FRIEND_MESSAGES["FRIENDS_RETRIEVED"],
    )


@router.delete("/friends/{friend_id}", status_code=204)
async def unfriend(
    friend_id: str,
    current_user: User = Depends(get_current_user),
    service: FriendService = Depends(_get_service),
):
    await service.unfriend(current_user.id, friend_id)
    # Real-time: notify both parties so their friends lists update instantly
    await ws_manager.send_to_user(
        friend_id,
        {"type": "friend_removed", "data": {"user_id": current_user.id}},
    )
    await ws_manager.send_to_user(
        current_user.id,
        {"type": "friend_removed", "data": {"user_id": friend_id}},
    )
