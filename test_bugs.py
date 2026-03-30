"""API smoke-test for all 6 permission / meaning bugs."""
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
            return {"status_code": e.code, "message": str(e)}


def main():
    # ── Login ──────────────────────────────────────────────────────────────────
    t1 = do("POST", "/auth/login", {"email": "admin@example.com", "password": "Admin@123"})["data"]["access_token"]
    t2 = do("POST", "/auth/login", {"email": "admin1@example.com", "password": "Admin@123"})["data"]["access_token"]
    u1 = do("GET", "/auth/me", token=t1)["data"]
    u2 = do("GET", "/auth/me", token=t2)["data"]
    print(f"User1: {u1['email']} ({u1['id']})")
    print(f"User2: {u2['email']} ({u2['id']})")

    # ── Setup: Book owned by User1 ─────────────────────────────────────────────
    book = do("POST", "/books", {"title": "TestBook-AllBugs", "visibility": "specific_users"}, t1)
    book_id = book["data"]["id"]
    do("POST", f"/permissions/book/{book_id}", {"user_id": u2["id"], "permission_level": "view"}, t1)
    print(f"\nCreated specific_users book {book_id}, shared with User2 (view)")

    # Private shlok (no explicit share with User2)
    priv = do("POST", "/shloks", {"book_id": book_id, "content": "Private shlok", "visibility": "private"}, t1)
    priv_id = priv["data"]["id"]
    # Specific_users shlok shared with User2 (request_edit)
    shared_shlok = do("POST", "/shloks", {"book_id": book_id, "content": "Shared shlok", "visibility": "specific_users"}, t1)
    shared_shlok_id = shared_shlok["data"]["id"]
    do("POST", f"/permissions/shlok/{shared_shlok_id}", {"user_id": u2["id"], "permission_level": "request_edit"}, t1)
    # Public shlok
    pub = do("POST", "/shloks", {"book_id": book_id, "content": "Public shlok", "visibility": "public"}, t1)
    pub_id = pub["data"]["id"]
    print(f"Private shlok: {priv_id}")
    print(f"Shared shlok (request_edit): {shared_shlok_id}")
    print(f"Public shlok: {pub_id}")

    # ── BUG 1: Private shlok must NOT appear in book listing for shared user ───
    print("\n=== Bug 1: Private shlok NOT in book listing for shared user ===")
    u2_list = do("GET", f"/shloks/book/{book_id}", token=t2)["data"]["items"]
    u2_ids = [s["id"] for s in u2_list]
    if priv_id in u2_ids:
        print(f"FAIL: private shlok {priv_id} is visible to User2 (should be hidden)")
    else:
        print("PASS: private shlok is NOT visible to shared user")
    if pub_id in u2_ids:
        print("PASS: public shlok IS visible to shared user")
    if shared_shlok_id in u2_ids:
        print("PASS: explicitly shared shlok IS visible to shared user")

    # ── BUG 2: Shlok response includes my_permission for shared user ──────────
    print("\n=== Bug 2: my_permission in shlok detail response ===")
    shlok_detail = do("GET", f"/shloks/{shared_shlok_id}", token=t2)["data"]
    perm = shlok_detail.get("my_permission")
    if perm == "request_edit":
        print(f"PASS: my_permission={perm} — frontend can show Edit button")
    else:
        print(f"FAIL: my_permission={perm} (expected 'request_edit')")

    # --- BUG 1 extra: private shlok should be blocked even if user had old explicit perm ---
    # Make shared_shlok private — User2 had explicit perm; should NOT see it now
    do("PATCH", f"/shloks/{shared_shlok_id}", {"visibility": "private"}, t1)
    u2_list2 = do("GET", f"/shloks/book/{book_id}", token=t2)["data"]["items"]
    if shared_shlok_id in [s["id"] for s in u2_list2]:
        print("FAIL Bug1-extra: shlok changed to private still visible to User2!")
    else:
        print("PASS Bug1-extra: shlok changed to private is now hidden from User2")
    # Restore visibility
    do("PATCH", f"/shloks/{shared_shlok_id}", {"visibility": "specific_users"}, t1)

    # ── Setup: Meanings ────────────────────────────────────────────────────────
    # Add public + private meanings to the shared shlok
    pub_meaning = do("POST", f"/shloks/{shared_shlok_id}/meanings", {"content": "Public meaning"}, t1)
    pub_meaning_id = pub_meaning["data"]["id"]
    do("PATCH", f"/meanings/{pub_meaning_id}", {"visibility": "public"}, t1)

    priv_meaning = do("POST", f"/shloks/{shared_shlok_id}/meanings", {"content": "Private meaning"}, t1)
    priv_meaning_id = priv_meaning["data"]["id"]
    # visibility stays private (default)

    # ── BUG 3: Private meanings must NOT appear for shared shlok viewer ────────
    print("\n=== Bug 3: Private meaning NOT visible to shared-shlok user ===")
    u2_meanings = do("GET", f"/shloks/{shared_shlok_id}/meanings", token=t2)["data"]["items"]
    meaning_ids_u2 = [m["id"] for m in u2_meanings]
    if priv_meaning_id in meaning_ids_u2:
        print(f"FAIL: private meaning {priv_meaning_id} visible to User2 (should be hidden)")
    else:
        print("PASS: private meaning is NOT visible to shared-shlok user")
    if pub_meaning_id in meaning_ids_u2:
        print("PASS: public meaning IS visible to shared-shlok user")

    # ── BUG 4: Child meanings appear in parent's children ─────────────────────
    print("\n=== Bug 4: Child meaning appears in parent.children ===")
    child = do("POST", f"/shloks/{shared_shlok_id}/meanings",
               {"content": "Reply to public meaning", "parent_id": pub_meaning_id}, t1)
    child_id = child.get("data", {}).get("id")
    print(f"Created child meaning: {child_id} under parent: {pub_meaning_id}")

    tree = do("GET", f"/shloks/{shared_shlok_id}/meanings", token=t1)["data"]["items"]
    def find_node(nodes, nid):
        for n in nodes:
            if n["id"] == nid:
                return n
            found = find_node(n.get("children", []), nid)
            if found:
                return found
        return None

    parent_node = find_node(tree, pub_meaning_id)
    if parent_node and child_id in [c["id"] for c in parent_node.get("children", [])]:
        print("PASS: child meaning appears in parent.children")
    else:
        print(f"FAIL: child {child_id} NOT found in parent.children={[c['id'] for c in (parent_node or {}).get('children', [])]}")

    # ── BUG 5: my_permission in meaning response for shared user ──────────────
    print("\n=== Bug 5: my_permission in meaning response ===")
    # Share the public meaning with User2 as request_edit
    do("POST", f"/permissions/meaning/{pub_meaning_id}", {"user_id": u2["id"], "permission_level": "request_edit"}, t1)
    do("PATCH", f"/meanings/{pub_meaning_id}", {"visibility": "specific_users"}, t1)
    u2_meanings2 = do("GET", f"/shloks/{shared_shlok_id}/meanings", token=t2)["data"]["items"]
    shared_m = find_node(u2_meanings2, pub_meaning_id)
    if shared_m:
        mp = shared_m.get("my_permission")
        if mp == "request_edit":
            print(f"PASS: meaning my_permission={mp} — frontend shows Edit button")
        else:
            print(f"FAIL: meaning my_permission={mp} (expected 'request_edit')")
    else:
        print(f"FAIL: shared meaning {pub_meaning_id} not found in User2's meaning list")

    # ── BUG 6: Parent visible when child meaning is shared ────────────────────
    print("\n=== Bug 6: Parent meaning visible when child is shared ===")
    # Create a private root meaning, then share only its child with User2
    priv_root = do("POST", f"/shloks/{shared_shlok_id}/meanings", {"content": "Private root (parent context)"}, t1)
    priv_root_id = priv_root["data"]["id"]  # visibility stays private

    shared_child = do("POST", f"/shloks/{shared_shlok_id}/meanings",
                      {"content": "Shared child of private parent", "parent_id": priv_root_id}, t1)
    shared_child_id = shared_child["data"]["id"]
    # Share the child with User2 and make it specific_users
    do("POST", f"/permissions/meaning/{shared_child_id}", {"user_id": u2["id"], "permission_level": "view"}, t1)
    do("PATCH", f"/meanings/{shared_child_id}", {"visibility": "specific_users"}, t1)

    u2_tree = do("GET", f"/shloks/{shared_shlok_id}/meanings", token=t2)["data"]["items"]
    parent_visible = find_node(u2_tree, priv_root_id)
    child_visible = find_node(u2_tree, shared_child_id)

    if child_visible:
        print("PASS: shared child meaning IS visible to User2")
    else:
        print("FAIL: shared child meaning is NOT visible to User2")

    if parent_visible:
        print("PASS: private parent IS visible to User2 as context for shared child")
    else:
        print("FAIL: private parent is NOT visible to User2 (Bug 6 not fixed!)")

    print("\nAll tests complete.")


if __name__ == "__main__":
    main()
