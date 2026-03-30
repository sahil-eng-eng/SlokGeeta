"""FriendRequest model — tracks pending / accepted / rejected friend connections."""

from sqlalchemy import String, Enum as SAEnum, UniqueConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import FriendRequestStatus


class FriendRequest(BaseModel):
    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request"),
        Index("ix_friend_request_receiver", "receiver_id"),
        Index("ix_friend_request_sender_status", "sender_id", "status"),
    )

    sender_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum(
            FriendRequestStatus,
            name="friend_request_status_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=FriendRequestStatus.PENDING,
        server_default=FriendRequestStatus.PENDING.value,
    )
