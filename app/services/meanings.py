"""Meaning service — business logic for meaning CRUD and voting."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.meanings import MeaningRepository
from app.repositories.shloks import ShlokRepository
from app.models.meaning import Meaning
from app.models.user import User
from app.schemas.meanings import (
    CreateMeaningRequest,
    InsertMeaningAboveRequest,
    InsertMeaningBelowRequest,
    UpdateMeaningRequest,
    MeaningResponse,
    MeaningListResponse,
)
from app.exceptions.meanings import MeaningNotFoundException, MeaningForbiddenException, MeaningCannotMakePrivateException
from app.exceptions.shloks import ShlokNotFoundException


class MeaningService:
    def __init__(self, db: AsyncSession):
        self.repo = MeaningRepository(db)
        self.shlok_repo = ShlokRepository(db)
        self.db = db

    async def _get_username(self, user_id: str) -> str:
        result = await self.db.execute(
            select(User.username).where(User.id == user_id)
        )
        username = result.scalar_one_or_none()
        return username or "Unknown"

    def _to_response(
        self,
        meaning: Meaning,
        viewer_id: Optional[str],
        author_map: dict[str, str],
        my_perm_map: Optional[dict[str, str]] = None,
    ) -> MeaningResponse:
        return MeaningResponse(
            id=meaning.id,
            shlok_id=meaning.shlok_id,
            parent_id=meaning.parent_id,
            author_id=meaning.author_id,
            text=meaning.content,
            author=author_map.get(meaning.author_id, "Unknown"),
            votes=meaning.vote_count,
            created_at=meaning.created_at,
            status=meaning.status,
            is_owner=(viewer_id == meaning.author_id),
            visibility=getattr(meaning, "visibility", "private") or "private",
            # Bug 5: Include viewer's permission level on this meaning
            my_permission=(my_perm_map or {}).get(meaning.id),
            reactions=[],
            versions=[],
            children=[
                self._to_response(child, viewer_id, author_map, my_perm_map)
                for child in sorted(
                    meaning.__dict__.get("children", []),
                    key=lambda c: (-c.vote_count, c.created_at),
                )
            ],
        )

    async def _build_author_map(self, meanings: list[Meaning]) -> dict[str, str]:
        """Collect all distinct author IDs from the tree and resolve usernames.

        Uses __dict__ access for children to avoid triggering SQLAlchemy lazy
        loads outside the async greenlet (MissingGreenlet safeguard).
        """
        author_ids: set[str] = set()

        def collect(nodes: list[Meaning]) -> None:
            for m in nodes:
                author_ids.add(m.author_id)
                # Safe: only traverse already-built children (set in __dict__)
                loaded_children = m.__dict__.get("children", [])
                collect(loaded_children)

        collect(meanings)

        if not author_ids:
            return {}

        result = await self.db.execute(
            select(User.id, User.username).where(User.id.in_(author_ids))
        )
        return {row.id: row.username for row in result.all()}

    # ── Public API ──────────────────────────────────────────

    async def create_meaning(
        self, shlok_id: str, author_id: str, data: CreateMeaningRequest
    ) -> MeaningResponse:
        shlok = await self.shlok_repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()

        if data.parent_id:
            parent = await self.repo.get_by_id(data.parent_id)
            if not parent or parent.shlok_id != shlok_id:
                raise MeaningNotFoundException()

        meaning = Meaning(
            shlok_id=shlok_id,
            parent_id=data.parent_id,
            author_id=author_id,
            content=data.content,
        )
        created = await self.repo.create(meaning)
        author_map = await self._build_author_map([created])
        return self._to_response(created, author_id, author_map)

    async def insert_meaning_above(
        self, shlok_id: str, author_id: str, data: InsertMeaningAboveRequest
    ) -> MeaningResponse:
        """Insert a new meaning directly above an existing one (same parent, same shlok)."""
        shlok = await self.shlok_repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()

        target = await self.repo.get_by_id(data.target_meaning_id)
        if not target or target.shlok_id != shlok_id:
            raise MeaningNotFoundException()

        new_meaning = Meaning(
            shlok_id=shlok_id,
            parent_id=target.parent_id,
            author_id=author_id,
            content=data.content,
        )
        created = await self.repo.insert_above(
            shlok_id=shlok_id,
            parent_id=target.parent_id,
            target_order=target.order_index,
            new_meaning=new_meaning,
        )
        author_map = await self._build_author_map([created])
        return self._to_response(created, author_id, author_map)

    async def insert_meaning_below(
        self, shlok_id: str, author_id: str, data: InsertMeaningBelowRequest
    ) -> MeaningResponse:
        """Insert a new meaning directly below an existing one (same parent, same shlok)."""
        shlok = await self.shlok_repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()

        target = await self.repo.get_by_id(data.target_meaning_id)
        if not target or target.shlok_id != shlok_id:
            raise MeaningNotFoundException()

        new_meaning = Meaning(
            shlok_id=shlok_id,
            parent_id=target.parent_id,
            author_id=author_id,
            content=data.content,
        )
        created = await self.repo.insert_below(
            shlok_id=shlok_id,
            parent_id=target.parent_id,
            target_order=target.order_index,
            new_meaning=new_meaning,
        )
        author_map = await self._build_author_map([created])
        return self._to_response(created, author_id, author_map)

    async def get_meanings_tree(
        self, shlok_id: str, viewer_id: Optional[str] = None
    ) -> MeaningListResponse:
        """Return the filtered meaning tree for a viewer.

        Fixes:
        - Bug 3: private meanings are hidden from non-author viewers
        - Bug 4: child meanings now appear (flat fetch + Python tree build)
        - Bug 5: my_permission included so frontend can gate Edit buttons
        - Bug 6: ancestors of visible meanings are always included for context
        """
        from app.constants.enums import EntityType, Visibility

        shlok = await self.shlok_repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()

        # Fetch ALL meanings as a flat list.
        # This avoids the SQLAlchemy async selectin recursion issue (Bug 4) and
        # allows us to apply visibility/permission filtering cleanly (Bug 3).
        all_meanings = await self.repo.get_all_by_shlok(shlok_id)
        if not all_meanings:
            return MeaningListResponse(items=[])

        # Resolve viewer's meaning-level entity permissions
        viewer_perm_map: dict[str, str] = {}  # meaning_id -> permission_level
        if viewer_id:
            from app.repositories.entity_permissions import EntityPermissionRepository
            perm_repo = EntityPermissionRepository(self.db)
            meaning_perms = await perm_repo.list_non_structural_for_user(
                viewer_id, EntityType.MEANING
            )
            viewer_perm_map = {
                p.entity_id: p.permission_level
                for p in meaning_perms
                if not p.is_hidden
            }

        is_shlok_owner = viewer_id is not None and shlok.owner_id == viewer_id

        def can_see(m: Meaning) -> bool:
            """True if the viewer has direct access to this meaning."""
            visibility = getattr(m, "visibility", "private") or "private"
            if visibility == Visibility.PUBLIC.value:
                return True
            # The author of the meaning always sees it
            if viewer_id and m.author_id == viewer_id:
                return True
            # Shlok owner sees all meanings in their shlok
            if is_shlok_owner:
                return True
            # specific_users: viewer must have an explicit entity_permission
            if (
                viewer_id
                and visibility == Visibility.SPECIFIC_USERS.value
                and m.id in viewer_perm_map
            ):
                return True
            return False

        # Build initial visible set
        visible_ids: set[str] = {m.id for m in all_meanings if can_see(m)}

        # Bug 6: Promote ancestors of visible meanings to visible so the viewer
        # has context for shared children (even if the parent is private).
        id_to_meaning: dict[str, Meaning] = {m.id: m for m in all_meanings}
        changed = True
        while changed:
            changed = False
            for m in all_meanings:
                if (
                    m.id in visible_ids
                    and m.parent_id
                    and m.parent_id not in visible_ids
                    and m.parent_id in id_to_meaning
                ):
                    visible_ids.add(m.parent_id)
                    changed = True

        visible_meanings = [m for m in all_meanings if m.id in visible_ids]

        # Reset children on every meaning to a plain list so we can build the
        # filtered tree ourselves (bypasses SQLAlchemy's InstrumentedList).
        for m in all_meanings:
            m.__dict__["children"] = []

        # Attach each visible meaning to its visible parent (or mark as root)
        roots: list[Meaning] = []
        for m in visible_meanings:
            if m.parent_id is None:
                roots.append(m)
            elif m.parent_id in id_to_meaning and m.parent_id in visible_ids:
                id_to_meaning[m.parent_id].__dict__["children"].append(m)
            else:
                # Orphan (e.g. parent outside this shlok) — promote to root
                roots.append(m)

        # Sort roots and each node's children by order_index asc, then created_at asc
        def sort_list(nodes: list[Meaning]) -> list[Meaning]:
            return sorted(nodes, key=lambda c: (c.order_index, c.created_at))

        roots = sort_list(roots)
        for m in visible_meanings:
            m.__dict__["children"] = sort_list(m.__dict__.get("children", []))

        author_map = await self._build_author_map(roots)
        items = [
            self._to_response(r, viewer_id, author_map, viewer_perm_map)
            for r in roots
        ]
        return MeaningListResponse(items=items)

    async def update_meaning(
        self, meaning_id: str, user_id: str, data: UpdateMeaningRequest
    ) -> MeaningResponse:
        meaning = await self.repo.get_by_id(meaning_id)
        if not meaning:
            raise MeaningNotFoundException()
        if meaning.author_id != user_id:
            # Bug 5: allow users with direct_edit permission to update directly
            from app.repositories.entity_permissions import EntityPermissionRepository
            from app.constants.enums import PermissionLevel
            perm_repo = EntityPermissionRepository(self.db)
            perm = await perm_repo.get(user_id, "meaning", meaning_id)
            if not (
                perm
                and not perm.is_hidden
                and not perm.is_structural
                and perm.permission_level == PermissionLevel.DIRECT_EDIT.value
            ):
                raise MeaningForbiddenException()

        updates = data.model_dump(exclude_unset=True)
        # Block changing to private when descendants are still shared
        if updates.get("visibility") == "private":
            descendant_ids = await self.repo.get_descendant_ids(meaning_id, meaning.shlok_id)
            if descendant_ids:
                from app.repositories.entity_permissions import EntityPermissionRepository
                perm_repo = EntityPermissionRepository(self.db)
                if await perm_repo.has_active_permissions_for_any("meaning", descendant_ids):
                    raise MeaningCannotMakePrivateException()
        if updates:
            updated = await self.repo.update(meaning_id, **updates)
        else:
            updated = meaning
        author_map = await self._build_author_map([updated])  # type: ignore[arg-type]
        return self._to_response(updated, user_id, author_map)  # type: ignore[arg-type]

    async def delete_meaning(self, meaning_id: str, user_id: str) -> None:
        meaning = await self.repo.get_by_id(meaning_id)
        if not meaning:
            raise MeaningNotFoundException()
        if meaning.author_id != user_id:
            raise MeaningForbiddenException()
        await self.repo.delete(meaning_id)

    async def vote_meaning(
        self, meaning_id: str, user_id: str, direction: int
    ) -> MeaningResponse:
        meaning = await self.repo.get_by_id(meaning_id)
        if not meaning:
            raise MeaningNotFoundException()

        # Allow direction -1, 0, or 1 — 0 removes the vote (no-op for now)
        delta = max(-1, min(1, direction))
        updated = await self.repo.adjust_vote(meaning_id, delta)
        author_map = await self._build_author_map([updated])  # type: ignore[arg-type]
        return self._to_response(updated, user_id, author_map)  # type: ignore[arg-type]
