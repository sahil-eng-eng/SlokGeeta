"""KirtanTrack model — personal kirtan/bhajan library."""

from sqlalchemy import String, Text, Integer, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import KirtanCategory


class KirtanTrack(BaseModel):
    __tablename__ = "kirtan_tracks"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[str] = mapped_column(String(255), nullable=True)
    album: Mapped[str] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(
        SAEnum(
            KirtanCategory,
            name="kirtan_category_enum",
            create_constraint=True,
            create_type=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=KirtanCategory.KIRTAN,
        server_default=KirtanCategory.KIRTAN.value,
        nullable=False,
    )
    audio_url: Mapped[str] = mapped_column(Text, nullable=True)
    external_link: Mapped[str] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
