"""Cursor-based pagination helpers."""

from typing import Optional, Tuple
from datetime import datetime
import base64


def encode_cursor(created_at: datetime, entity_id: str) -> str:
    raw = f"{created_at.isoformat()}|{entity_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> Optional[Tuple[datetime, str]]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        parts = raw.split("|", 1)
        if len(parts) != 2:
            return None
        ts = datetime.fromisoformat(parts[0])
        return (ts, parts[1])
    except Exception:
        return None
