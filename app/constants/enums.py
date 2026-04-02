"""Application-wide enumerations."""

import enum


class Visibility(str, enum.Enum):
    PRIVATE = "private"
    SPECIFIC_USERS = "specific_users"
    PUBLIC = "public"


class PermissionRole(str, enum.Enum):
    VIEWER = "viewer"
    SUGGESTER = "suggester"
    EDITOR = "editor"
    CO_OWNER = "co_owner"


class EntityType(str, enum.Enum):
    BOOK = "book"
    SHLOK = "shlok"
    MEANING = "meaning"


class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"


class ApprovalStatus(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


# ── Friends ────────────────────────────────────────────────────────────────────

class FriendRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# ── Chat ───────────────────────────────────────────────────────────────────────

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    SEEN = "seen"


# ── Shared links ───────────────────────────────────────────────────────────────

class LinkTargetType(str, enum.Enum):
    BOOK = "book"
    SHLOK = "shlok"
    MEANING = "meaning"


# ── Content requests / approval workflow ──────────────────────────────────────

class ContentAction(str, enum.Enum):
    VIEW = "view"
    ADD_SHLOK = "add_shlok"
    ADD_MEANING = "add_meaning"
    EDIT = "edit"
    DELETE = "delete"


class PermissionLevel(str, enum.Enum):
    """Three-tier sharing permission: what a recipient can do with a shared entity."""
    VIEW = "view"            # Read-only access
    REQUEST_EDIT = "request_edit"  # Propose changes via approval workflow
    DIRECT_EDIT = "direct_edit"   # Apply changes immediately


class ContentRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ── Kirtan Library ─────────────────────────────────────────────────────────────

class KirtanCategory(str, enum.Enum):
    BHAJAN = "bhajan"
    AARTI = "aarti"
    KIRTAN = "kirtan"
    DHUN = "dhun"
    STUTI = "stuti"
    OTHER = "other"


# ── User roles ─────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
