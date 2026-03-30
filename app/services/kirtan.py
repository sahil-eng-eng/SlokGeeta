"""Kirtan Library service — business logic."""

import re
import asyncio

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import create_client

from app.core.config import get_settings
from app.repositories.kirtan import KirtanRepository
from app.models.kirtan_track import KirtanTrack
from app.schemas.kirtan import CreateKirtanTrackRequest, KirtanTrackResponse


class KirtanNotFoundException(Exception):
    pass


class KirtanForbiddenException(Exception):
    pass


class KirtanInvalidFileException(Exception):
    pass


class KirtanService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = KirtanRepository(db)

    def _to_response(self, track: KirtanTrack) -> KirtanTrackResponse:
        return KirtanTrackResponse(
            id=track.id,
            owner_id=track.owner_id,
            title=track.title,
            artist=track.artist,
            album=track.album,
            duration_seconds=track.duration_seconds,
            category=track.category,
            audio_url=track.audio_url,
            external_link=track.external_link,
            cover_url=track.cover_url,
            is_favorite=track.is_favorite,
        )

    async def list_tracks(self, owner_id: str) -> list[KirtanTrackResponse]:
        tracks = await self.repo.list_by_owner(owner_id)
        return [self._to_response(t) for t in tracks]

    async def create_track(
        self, owner_id: str, data: CreateKirtanTrackRequest
    ) -> KirtanTrackResponse:
        track = KirtanTrack(
            owner_id=owner_id,
            title=data.title,
            artist=data.artist,
            album=data.album,
            duration_seconds=data.duration_seconds,
            category=data.category.value if data.category else "kirtan",
            audio_url=data.audio_url,
            external_link=data.external_link,
            cover_url=data.cover_url,
            is_favorite=False,
        )
        created = await self.repo.create(track)
        return self._to_response(created)

    async def toggle_favorite(
        self, track_id: str, owner_id: str
    ) -> KirtanTrackResponse:
        track = await self.repo.get_by_id(track_id)
        if not track:
            raise KirtanNotFoundException()
        if track.owner_id != owner_id:
            raise KirtanForbiddenException()
        track.is_favorite = not track.is_favorite
        saved = await self.repo.save(track)
        return self._to_response(saved)

    async def delete_track(self, track_id: str, owner_id: str) -> None:
        track = await self.repo.get_by_id(track_id)
        if not track:
            raise KirtanNotFoundException()
        if track.owner_id != owner_id:
            raise KirtanForbiddenException()
        await self.repo.delete(track)

    async def upload_audio(
        self, track_id: str, owner_id: str, file: UploadFile
    ) -> KirtanTrackResponse:
        track = await self.repo.get_by_id(track_id)
        if not track:
            raise KirtanNotFoundException()
        if track.owner_id != owner_id:
            raise KirtanForbiddenException()

        content_type = file.content_type or ""
        if not content_type.startswith("audio/"):
            raise KirtanInvalidFileException("Only audio files are allowed")

        contents = await file.read()
        safe_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename or "audio")
        storage_path = f"{owner_id}/{track_id}/{safe_filename}"

        def _upload() -> None:
            settings = get_settings()
            client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
            )
            client.storage.from_("kirtan-audio").upload(
                path=storage_path,
                file=contents,
                file_options={"content-type": content_type, "upsert": "true"},
            )

        await asyncio.to_thread(_upload)

        settings = get_settings()
        public_url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/kirtan-audio/{storage_path}"
        )
        track.audio_url = public_url
        saved = await self.repo.save(track)
        return self._to_response(saved)
