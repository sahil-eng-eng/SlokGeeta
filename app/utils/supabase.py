"""Supabase Storage helpers for file upload and deletion."""

import httpx
from app.core.config import get_settings

settings = get_settings()

BUCKETS = {
    "book-covers": "book-covers",
    "shlok-audio": "shlok-audio",
    "export-cards": "export-cards",
    "avatars": "avatars",
}


async def upload_file(
    bucket: str, path: str, file_bytes: bytes, content_type: str
) -> str:
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=file_bytes, headers=headers)
        resp.raise_for_status()
    return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"


async def delete_file(bucket: str, paths: list[str]) -> None:
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        await client.request(
            "DELETE", url, json={"prefixes": paths}, headers=headers
        )
