"""Meaning repository — data access for the Meaning model."""

from typing import Optional
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meaning import Meaning


class MeaningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, meaning: Meaning) -> Meaning:
        # If no order_index set, place at end among siblings
        if meaning.order_index == 0:
            max_idx = await self._max_order_index(
                meaning.shlok_id, meaning.parent_id
            )
            meaning.order_index = max_idx + 1
        self.db.add(meaning)
        await self.db.flush()
        # Re-fetch so that selectin-loaded children are initialised
        return await self.get_by_id(meaning.id)  # type: ignore[return-value]

    async def _max_order_index(
        self, shlok_id: str, parent_id: Optional[str]
    ) -> int:
        """Return the current max order_index among siblings (same parent_id)."""
        q = select(func.coalesce(func.max(Meaning.order_index), 0)).where(
            Meaning.shlok_id == shlok_id
        )
        if parent_id is None:
            q = q.where(Meaning.parent_id.is_(None))
        else:
            q = q.where(Meaning.parent_id == parent_id)
        result = await self.db.execute(q)
        return result.scalar_one()

    async def insert_above(
        self,
        shlok_id: str,
        parent_id: Optional[str],
        target_order: int,
        new_meaning: Meaning,
    ) -> Meaning:
        """Insert a new meaning above a sibling that has order_index == target_order.

        All siblings with order_index >= target_order get shifted up by 1.
        The new meaning takes  order_index = target_order.
        """
        # Shift siblings at or after target_order
        shift_q = (
            update(Meaning)
            .where(Meaning.shlok_id == shlok_id)
            .where(
                Meaning.parent_id == parent_id
                if parent_id is not None
                else Meaning.parent_id.is_(None)
            )
            .where(Meaning.order_index >= target_order)
            .values(order_index=Meaning.order_index + 1)
        )
        await self.db.execute(shift_q)
        await self.db.flush()

        new_meaning.order_index = target_order
        return await self.create(new_meaning)

    async def insert_below(
        self,
        shlok_id: str,
        parent_id: Optional[str],
        target_order: int,
        new_meaning: Meaning,
    ) -> Meaning:
        """Insert a new meaning below a sibling that has order_index == target_order.

        All siblings with order_index > target_order get shifted up by 1.
        The new meaning takes order_index = target_order + 1.
        """
        insert_at = target_order + 1
        shift_q = (
            update(Meaning)
            .where(Meaning.shlok_id == shlok_id)
            .where(
                Meaning.parent_id == parent_id
                if parent_id is not None
                else Meaning.parent_id.is_(None)
            )
            .where(Meaning.order_index >= insert_at)
            .values(order_index=Meaning.order_index + 1)
        )
        await self.db.execute(shift_q)
        await self.db.flush()

        new_meaning.order_index = insert_at
        return await self.create(new_meaning)

    async def get_by_id(self, meaning_id: str) -> Optional[Meaning]:
        result = await self.db.execute(
            select(Meaning).where(Meaning.id == meaning_id)
        )
        return result.scalar_one_or_none()

    async def get_roots_by_shlok(self, shlok_id: str) -> list[Meaning]:
        """Return only root-level meanings (parent_id IS NULL) for a shlok.
        SQLAlchemy's selectin loader will recursively load all children."""
        result = await self.db.execute(
            select(Meaning)
            .where(Meaning.shlok_id == shlok_id, Meaning.parent_id.is_(None))
            .order_by(Meaning.vote_count.desc(), Meaning.created_at.asc())
        )
        return list(result.scalars().all())

    async def update(self, meaning_id: str, **kwargs) -> Optional[Meaning]:
        await self.db.execute(
            update(Meaning).where(Meaning.id == meaning_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_by_id(meaning_id)

    async def delete(self, meaning_id: str) -> None:
        await self.db.execute(delete(Meaning).where(Meaning.id == meaning_id))
        await self.db.flush()

    async def adjust_vote(self, meaning_id: str, delta: int) -> Optional[Meaning]:
        await self.db.execute(
            update(Meaning)
            .where(Meaning.id == meaning_id)
            .values(vote_count=Meaning.vote_count + delta)
        )
        await self.db.flush()
        return await self.get_by_id(meaning_id)

    async def get_all_by_shlok(self, shlok_id: str) -> list[Meaning]:
        """Return ALL meanings for a shlok as a flat unordered list.
        Used to build a filtered tree in Python (avoids selectin recursion issues
        and enables visibility / permission filtering).
        """
        result = await self.db.execute(
            select(Meaning).where(Meaning.shlok_id == shlok_id)
        )
        return list(result.scalars().all())

    async def get_all_ids_by_shlok(self, shlok_id: str) -> list[str]:
        """Return all meaning IDs for a shlok (any depth) — IDs only."""
        result = await self.db.execute(
            select(Meaning.id).where(Meaning.shlok_id == shlok_id)
        )
        return list(result.scalars().all())

    async def get_descendant_ids(self, meaning_id: str, shlok_id: str) -> list[str]:
        """Return IDs of all descendant meanings (replies and deeper) of a given meaning."""
        all_rows = await self.db.execute(
            select(Meaning.id, Meaning.parent_id).where(Meaning.shlok_id == shlok_id)
        )
        rows = all_rows.all()  # list of (id, parent_id)
        children_map: dict[str, list[str]] = {}
        for row_id, row_parent in rows:
            if row_parent:
                children_map.setdefault(row_parent, []).append(row_id)
        # BFS from meaning_id
        result_ids: list[str] = []
        queue = [meaning_id]
        while queue:
            current = queue.pop()
            for child_id in children_map.get(current, []):
                result_ids.append(child_id)
                queue.append(child_id)
        return result_ids
