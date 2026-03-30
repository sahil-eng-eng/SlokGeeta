"""Shlok repository — data access for Shlok and ShlokCrossReference."""

from typing import Optional
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shlok import Shlok, ShlokCrossReference
from app.constants.enums import Visibility
from app.utils.pagination import decode_cursor


class ShlokRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, shlok: Shlok) -> Shlok:
        self.db.add(shlok)
        await self.db.flush()
        return shlok

    async def get_by_id(self, shlok_id: str) -> Optional[Shlok]:
        result = await self.db.execute(select(Shlok).where(Shlok.id == shlok_id))
        return result.scalar_one_or_none()

    async def update(self, shlok_id: str, **kwargs) -> Optional[Shlok]:
        await self.db.execute(
            update(Shlok).where(Shlok.id == shlok_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_by_id(shlok_id)

    async def delete(self, shlok_id: str) -> None:
        await self.db.execute(delete(Shlok).where(Shlok.id == shlok_id))
        await self.db.flush()

    async def increment_view(self, shlok_id: str) -> None:
        await self.db.execute(
            update(Shlok)
            .where(Shlok.id == shlok_id)
            .values(view_count=Shlok.view_count + 1)
        )
        await self.db.flush()

    async def get_all_ids_by_book(self, book_id: str) -> list[str]:
        """Return all shlok IDs for a book — IDs only."""
        result = await self.db.execute(
            select(Shlok.id).where(Shlok.book_id == book_id)
        )
        return list(result.scalars().all())

    async def list_by_book(
        self, book_id: str, cursor: Optional[str] = None, limit: int = 20
    ) -> list[Shlok]:
        query = (
            select(Shlok)
            .where(Shlok.book_id == book_id)
            .order_by(
                Shlok.chapter_number.asc().nullslast(),
                Shlok.verse_number.asc().nullslast(),
                Shlok.created_at.desc(),
            )
        )
        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                ts, cid = decoded
                query = query.where(
                    or_(
                        Shlok.created_at < ts,
                        and_(Shlok.created_at == ts, Shlok.id < cid),
                    )
                )
        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_book_for_nonowner(
        self,
        book_id: str,
        explicit_shlok_ids: list[str],
        structural_shlok_ids: list[str],
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> list[Shlok]:
        """List shloks visible to a non-owner:
        - public shloks (visibility = 'public')
        - specific_users shloks where viewer has explicit entity_permission
        - shloks with structural (navigation) access via a shared child meaning
        NOTE: private shloks are never shown to non-owners even if they have
              old explicit permissions (setting back to private revokes visibility).
        """
        query = (
            select(Shlok)
            .where(
                Shlok.book_id == book_id,
                or_(
                    Shlok.visibility == Visibility.PUBLIC.value,
                    and_(
                        Shlok.visibility == Visibility.SPECIFIC_USERS.value,
                        Shlok.id.in_(explicit_shlok_ids),
                    ),
                    Shlok.id.in_(structural_shlok_ids),
                ),
            )
            .order_by(
                Shlok.chapter_number.asc().nullslast(),
                Shlok.verse_number.asc().nullslast(),
                Shlok.created_at.desc(),
            )
        )
        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                ts, cid = decoded
                query = query.where(
                    or_(
                        Shlok.created_at < ts,
                        and_(Shlok.created_at == ts, Shlok.id < cid),
                    )
                )
        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_owner(
        self, owner_id: str, cursor: Optional[str] = None, limit: int = 20
    ) -> list[Shlok]:
        query = (
            select(Shlok)
            .where(Shlok.owner_id == owner_id)
            .order_by(Shlok.created_at.desc(), Shlok.id.desc())
        )
        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                ts, cid = decoded
                query = query.where(
                    or_(
                        Shlok.created_at < ts,
                        and_(Shlok.created_at == ts, Shlok.id < cid),
                    )
                )
        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_scheduled_for_publish(self, now: datetime) -> list[Shlok]:
        result = await self.db.execute(
            select(Shlok).where(
                Shlok.scheduled_at != None,  # noqa: E711
                Shlok.scheduled_at <= now,
                Shlok.visibility != Visibility.PUBLIC,
            )
        )
        return list(result.scalars().all())

    async def get_related_shloks(
        self, shlok: Shlok, limit: int = 10
    ) -> list[Shlok]:
        """Related shloks scored by shared_tags*2 + same_book*3 + same_author*1."""
        tags_array = (
            "{" + ",".join(shlok.tags) + "}" if shlok.tags else "{}"
        )
        query = text(
            """
            SELECT s.*,
                (COALESCE(array_length(ARRAY(
                    SELECT unnest(s.tags) INTERSECT SELECT unnest(:tags::text[])
                ), 1), 0) * 2) +
                (CASE WHEN s.book_id = :book_id THEN 3 ELSE 0 END) +
                (CASE WHEN s.owner_id = :owner_id THEN 1 ELSE 0 END) AS relevance_score
            FROM shloks s
            WHERE s.id != :shlok_id
              AND s.visibility = 'public'
            ORDER BY relevance_score DESC, s.created_at DESC
            LIMIT :limit
            """
        )
        result = await self.db.execute(
            query,
            {
                "tags": tags_array,
                "book_id": shlok.book_id,
                "owner_id": shlok.owner_id,
                "shlok_id": shlok.id,
                "limit": limit,
            },
        )
        rows = result.fetchall()
        shlok_ids = [r[0] for r in rows]
        if not shlok_ids:
            return []
        res = await self.db.execute(select(Shlok).where(Shlok.id.in_(shlok_ids)))
        return list(res.scalars().all())

    # ── Cross References ─────────────────────────────────────────

    async def add_cross_reference(
        self, ref: ShlokCrossReference
    ) -> ShlokCrossReference:
        self.db.add(ref)
        await self.db.flush()
        return ref

    async def get_cross_references(
        self, shlok_id: str
    ) -> list[ShlokCrossReference]:
        result = await self.db.execute(
            select(ShlokCrossReference).where(
                or_(
                    ShlokCrossReference.source_shlok_id == shlok_id,
                    ShlokCrossReference.target_shlok_id == shlok_id,
                )
            )
        )
        return list(result.scalars().all())

    async def delete_cross_reference(self, ref_id: str) -> None:
        await self.db.execute(
            delete(ShlokCrossReference).where(ShlokCrossReference.id == ref_id)
        )
        await self.db.flush()
