# ShlokVault API Reference

**Base URL:** `http://localhost:8000/api/v1`

All responses follow the shape:
```json
{
  "status_code": 200,
  "message": "Description",
  "data": { ... }
}
```

---

## Health

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Returns `{"status": "ok"}` |

---

## Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register with email, username, full_name, password |
| POST | `/auth/verify-email` | No | Verify email with OTP token |
| POST | `/auth/resend-otp` | No | Resend OTP to email |
| POST | `/auth/login` | No | Login with email + password → access + refresh tokens |
| POST | `/auth/google` | No | Google OAuth login via id_token |
| POST | `/auth/refresh` | No | Rotate refresh token → new access + refresh tokens |
| POST | `/auth/logout` | No | Revoke a single refresh token |
| POST | `/auth/logout-all` | Yes | Revoke all refresh tokens for user |
| POST | `/auth/forgot-password` | No | Send password reset email |
| POST | `/auth/reset-password` | No | Reset password with token |
| POST | `/auth/change-password` | Yes | Change password (requires current password) |
| GET  | `/auth/me` | Yes | Get current user profile |
| PATCH | `/auth/me` | Yes | Update profile (full_name, username, bio) |
| POST | `/auth/me/avatar` | Yes | Upload avatar image |

### Register
```
POST /auth/register
Body: { "email": "...", "username": "...", "full_name": "...", "password": "..." }
→ 201 { "data": UserResponse }
```

### Login
```
POST /auth/login
Body: { "email": "...", "password": "...", "remember_me": false }
→ 200 { "data": { "access_token": "...", "refresh_token": "...", "user": UserResponse } }
```

### Verify Email
```
POST /auth/verify-email
Body: { "token": "otp-token-from-email" }
→ 200
```

### Forgot Password
```
POST /auth/forgot-password
Body: { "email": "..." }
→ 200 (always succeeds to prevent email enumeration)
```

### Reset Password
```
POST /auth/reset-password
Body: { "token": "...", "new_password": "..." }
→ 200
```

---

## Books

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/books` | Yes | Create a book |
| GET | `/books/me` | Yes | List my books (cursor pagination) |
| GET | `/books/public` | No | List public books (cursor pagination) |
| GET | `/books/{book_id}` | Optional | Get a book (respects visibility) |
| PATCH | `/books/{book_id}` | Yes | Update a book (owner or editor) |
| DELETE | `/books/{book_id}` | Yes | Delete a book (owner only) |
| POST | `/books/{book_id}/cover` | Yes | Upload cover image |

### Create Book
```
POST /books
Body: {
  "title": "...",
  "description": "...",
  "category": "...",
  "tags": ["..."],
  "source": "...",
  "author_name": "...",
  "visibility": "private" | "public" | "specific_users"
}
→ 201 { "data": BookResponse }
```

### List My Books
```
GET /books/me?cursor=xxx&limit=20
→ 200 { "data": { "items": [BookResponse], "next_cursor": "...", "has_more": true } }
```

---

## Shloks

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/shloks` | Yes | Create a shlok in a book |
| GET | `/shloks/book/{book_id}` | Optional | List shloks by book (cursor pagination) |
| GET | `/shloks/{shlok_id}` | Optional | Get a shlok (respects visibility) |
| PATCH | `/shloks/{shlok_id}` | Yes | Update a shlok (owner or editor) |
| DELETE | `/shloks/{shlok_id}` | Yes | Delete a shlok (owner only) |
| POST | `/shloks/{shlok_id}/audio` | Yes | Upload audio file |
| GET | `/shloks/{shlok_id}/related` | No | Get related shloks by relevance |
| POST | `/shloks/{shlok_id}/cross-references` | Yes | Add cross-reference |
| GET | `/shloks/{shlok_id}/cross-references` | No | List cross-references |

### Create Shlok
```
POST /shloks
Body: {
  "book_id": "...",
  "content": "...",
  "chapter_number": 1,
  "verse_number": 1,
  "tags": ["..."],
  "visibility": "private",
  "scheduled_at": null
}
→ 201 { "data": ShlokResponse }
```

---

## Data Models

### UserResponse
```json
{
  "id": "uuid",
  "email": "string",
  "username": "string",
  "full_name": "string",
  "avatar_url": "string | null",
  "bio": "string | null",
  "is_verified": true,
  "auth_provider": "email | google",
  "created_at": "datetime"
}
```

### BookResponse
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "title": "string",
  "description": "string | null",
  "cover_image_url": "string | null",
  "category": "string | null",
  "tags": ["string"],
  "source": "string | null",
  "author_name": "string | null",
  "visibility": "private | public | specific_users",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### ShlokResponse
```json
{
  "id": "uuid",
  "book_id": "uuid",
  "owner_id": "uuid",
  "content": "string",
  "chapter_number": "int | null",
  "verse_number": "int | null",
  "tags": ["string"],
  "audio_url": "string | null",
  "visibility": "private | public | specific_users",
  "scheduled_at": "datetime | null",
  "view_count": 0,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Error Codes

| Status | Meaning |
|---|---|
| 400 | Bad request / validation error |
| 401 | Unauthorized (missing/expired token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |
| 409 | Conflict (duplicate email/username) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| POST `/auth/register` | 5/minute |
| POST `/auth/login` | 10/minute |
| POST `/auth/resend-otp` | 3/minute |
| POST `/auth/forgot-password` | 3/minute |
