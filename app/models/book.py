"""Book model."""

from sqlalchemy import String, Text, Enum as SAEnum, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import Visibility


class Book(BaseModel):
    __tablename__ = "books"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(200), nullable=True)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")
    source: Mapped[str] = mapped_column(String(500), nullable=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=True)
    visibility: Mapped[str] = mapped_column(
        SAEnum(
            Visibility,
            name="visibility_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=Visibility.PRIVATE,
        server_default=Visibility.PRIVATE.value,
    )
