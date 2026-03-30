"""Smoke tests for the 3 new bugs."""
import urllib.request
import json

BASE = "http://localhost:8000/api/v1"


def do(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"status_code": e.code, "error": str(e)}


def main():
    t1 = do("POST", "/auth/login", {"email": "admin@example.com", "password": "Admin@123"})["data"]["access_token"]
    t2 = do("POST", "/auth/login", {"email": "admin1@example.com", "password": "Admin@123"})["data"]["access_token"]
    u2 = do("GET", "/auth/me", token=t2)["data"]

    # ── Bug 1: Share shlok from private book → book auto-upgraded ─────────────
    print("\n=== Bug 1: Auto-propagate parent book access when sharing shlok ===")
    book = do("POST", "/books", {"title": "PrivateBook-NewBug1", "visibility": "private"}, t1)
    book_id = book["data"]["id"]
    shlok = do("POST", "/shloks", {"book_id": book_id, "content": "Shlok in private book", "visibility": "specific_users"}, t1)
    shlok_id = shlok["data"]["id"]
    print(f"Created private book ({book_id}) and shlok ({shlok_id})")

    # Share shlok with user2 (view)
    do("POST", f"/permissions/shlok/{shlok_id}", {"user_id": u2["id"], "permission_level": "view"}, t1)

    # Book visibility should now be specific_users
    book_now = do("GET", f"/books/{book_id}", token=t1)["data"]
    if book_now["visibility"] == "specific_users":
        print("PASS: Book auto-upgraded from private to specific_users")
    else:
        print(f"FAIL: Book visibility is still {book_now['visibility']}")

    # User2 can access the book
    book_u2 = do("GET", f"/books/{book_id}", token=t2)
    if book_u2.get("data", {}).get("id"):
        print("PASS: User2 can now access the private→shared book")
    else:
        print(f"FAIL: User2 cannot access book: {book_u2.get('message')}")

    # User2 can see the shlok in book listing
    u2_shloks = do("GET", f"/shloks/book/{book_id}", token=t2)["data"]["items"]
    if any(s["id"] == shlok_id for s in u2_shloks):
        print("PASS: User2 can see the shared shlok in book listing")
    else:
        print("FAIL: User2 cannot see shlok in listing")

    # ── Bug 1b: Share meaning from private shlok/book → both auto-upgraded ────
    print("\n=== Bug 1b: Auto-propagate for meaning → shlok → book ===")
    book2 = do("POST", "/books", {"title": "PrivateBook-Bug1b", "visibility": "private"}, t1)
    book2_id = book2["data"]["id"]
    shlok2 = do("POST", "/shloks", {"book_id": book2_id, "content": "Private shlok", "visibility": "private"}, t1)
    shlok2_id = shlok2["data"]["id"]
    meaning = do("POST", f"/shloks/{shlok2_id}/meanings", {"content": "Private meaning"}, t1)
    meaning_id = meaning["data"]["id"]
    do("PATCH", f"/meanings/{meaning_id}", {"visibility": "specific_users"}, t1)

    # Share meaning with user2
    do("POST", f"/permissions/meaning/{meaning_id}", {"user_id": u2["id"], "permission_level": "view"}, t1)

    shlok2_now = do("GET", f"/shloks/{shlok2_id}", token=t1)["data"]
    book2_now = do("GET", f"/books/{book2_id}", token=t1)["data"]
    shlok_ok = shlok2_now["visibility"] == "specific_users"
    book_ok = book2_now["visibility"] == "specific_users"
    print(f"PASS: Shlok auto-upgraded" if shlok_ok else f"FAIL: Shlok still {shlok2_now['visibility']}")
    print(f"PASS: Book auto-upgraded" if book_ok else f"FAIL: Book still {book2_now['visibility']}")

    # ── Bug 2b: REQUEST_CREATED key fix ───────────────────────────────────────
    print("\n=== Bug 2b: Content request creation (no KeyError) ===")
    cr = do("POST", "/requests", {
        "entity_type": "shlok",
        "entity_id": shlok_id,
        "action": "edit",
        "proposed_content": {"content": "My suggested edit"},
    }, t2)
    if cr.get("data", {}).get("id"):
        print(f"PASS: Content request created, id={cr['data']['id']}")
    else:
        print(f"FAIL: {cr}")

    # ── Bug 2b: context_breadcrumb in incoming requests ───────────────────────
    print("\n=== Bug 2b: Incoming request has context breadcrumb ===")
    incoming = do("GET", "/requests/incoming", token=t1)
    items = incoming.get("data", [])
    if items:
        sample = items[0]
        bc = sample.get("context_breadcrumb")
        print(f"PASS: context_breadcrumb={bc}" if bc else "FAIL: context_breadcrumb missing or empty")
        ru = sample.get("requester_username")
        print(f"PASS: requester_username={ru}" if ru else "FAIL: requester_username missing")
    else:
        print("NOTE: No incoming requests to check (owner may have no requests)")

    # ── Bug 1 edge case: don't downgrade existing request_edit on book ────────
    print("\n=== Bug 1 edge case: Do NOT downgrade request_edit on parent ===")
    book3 = do("POST", "/books", {"title": "PrivateBook-NoDngrade", "visibility": "private"}, t1)
    book3_id = book3["data"]["id"]
    # Give user2 request_edit on the book first
    do("PATCH", f"/books/{book3_id}", {"visibility": "specific_users"}, t1)
    do("POST", f"/permissions/book/{book3_id}", {"user_id": u2["id"], "permission_level": "request_edit"}, t1)
    # Revert book to private
    do("PATCH", f"/books/{book3_id}", {"visibility": "private"}, t1)
    shlok3 = do("POST", "/shloks", {"book_id": book3_id, "content": "Shlok3", "visibility": "specific_users"}, t1)
    shlok3_id = shlok3["data"]["id"]
    # Share shlok with user2 (view) - should NOT downgrade book perm from request_edit
    do("POST", f"/permissions/shlok/{shlok3_id}", {"user_id": u2["id"], "permission_level": "view"}, t1)
    book3_perms = do("GET", f"/permissions/book/{book3_id}", token=t1)["data"]
    u2_perm = next((p for p in book3_perms if p["user_id"] == u2["id"] and not p["is_structural"]), None)
    if u2_perm and u2_perm["permission_level"] == "request_edit":
        print("PASS: Existing request_edit on book NOT downgraded to view")
    else:
        print(f"FAIL: Expected request_edit but got {u2_perm}")

    print("\nAll new bug tests complete.")


if __name__ == "__main__":
    main()
