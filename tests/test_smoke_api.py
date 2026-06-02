from pathlib import Path

from app.core.config import settings
from app.models.document import Document
from app.models.enums import UserRole

from tests.conftest import auth_header, create_user, login


import pytest


@pytest.mark.anyio
async def test_auth_smoke_flow(client, db_session):
    create_user(db_session, email="admin@gap.org", password="pass1234", role=UserRole.admin, name="Admin")

    login_data = await login(client, "admin@gap.org", "pass1234")
    access = login_data["accessToken"]
    refresh = login_data["refreshToken"]
    assert login_data["user"]["email"] == "admin@gap.org"

    me = await client.get("/api/v1/auth/me", headers=auth_header(access))
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "admin@gap.org"

    rf = await client.post("/api/v1/auth/refresh", json={"refreshToken": refresh})
    assert rf.status_code == 200
    new_refresh = rf.json()["data"]["refreshToken"]

    lo = await client.post("/api/v1/auth/logout", json={"refreshToken": new_refresh})
    assert lo.status_code == 200

    rf2 = await client.post("/api/v1/auth/refresh", json={"refreshToken": new_refresh})
    assert rf2.status_code == 401


@pytest.mark.anyio
async def test_user_avatar_upload_smoke(client, db_session):
    create_user(db_session, email="member@gap.org", password="pass1234", role=UserRole.member, name="Member")
    token = (await login(client, "member@gap.org", "pass1234"))["accessToken"]
    headers = auth_header(token)

    upload = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"fake-image-bytes", "image/png")},
    )
    assert upload.status_code == 200
    avatar_url = upload.json()["data"]["avatarUrl"]
    assert avatar_url.startswith("/uploads/avatars/")

    file_res = await client.get(avatar_url)
    assert file_res.status_code == 200
    assert file_res.content == b"fake-image-bytes"

    reset = await client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"avatarUrl": None},
    )
    assert reset.status_code == 200
    assert reset.json()["data"]["avatarUrl"] is None


@pytest.mark.anyio
async def test_user_password_change_smoke(client, db_session):
    create_user(db_session, email="member@gap.org", password="pass1234", role=UserRole.member, name="Member")
    token = (await login(client, "member@gap.org", "pass1234"))["accessToken"]
    headers = auth_header(token)

    wrong_current = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"currentPassword": "wrongpass", "newPassword": "newpass123"},
    )
    assert wrong_current.status_code == 401

    short_new = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"currentPassword": "pass1234", "newPassword": "short"},
    )
    assert short_new.status_code == 422

    same_new = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"currentPassword": "pass1234", "newPassword": "pass1234"},
    )
    assert same_new.status_code == 422

    success = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"currentPassword": "pass1234", "newPassword": "newpass123"},
    )
    assert success.status_code == 200
    assert success.json()["data"]["success"] is True

    old_login = await client.post("/api/v1/auth/login", json={"email": "member@gap.org", "password": "pass1234"})
    assert old_login.status_code == 401

    new_login = await client.post("/api/v1/auth/login", json={"email": "member@gap.org", "password": "newpass123"})
    assert new_login.status_code == 200


@pytest.mark.anyio
async def test_document_comment_reaction_smoke(client, db_session):
    create_user(db_session, email="member@gap.org", password="pass1234", role=UserRole.member, name="Member")
    token = (await login(client, "member@gap.org", "pass1234"))["accessToken"]
    headers = auth_header(token)

    created = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"title": "Doc A", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}], "status": "draft"},
    )
    assert created.status_code == 200
    doc_id = created.json()["data"]["id"]
    assert created.json()["data"]["ownerName"] == "Member"
    assert created.json()["data"]["owner"]["name"] == "Member"
    stored_doc = db_session.get(Document, doc_id)
    assert stored_doc is not None
    assert stored_doc.content_path == f"documents/{doc_id}.md"

    listed = await client.get("/api/v1/documents", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] >= 1
    assert listed.json()["data"][0]["ownerName"] == "Member"
    assert (Path(settings.document_storage_root) / stored_doc.content_path).exists()

    patched = await client.patch(f"/api/v1/documents/{doc_id}", headers=headers, json={"title": "Doc B", "status": "published"})
    assert patched.status_code == 200
    assert patched.json()["data"]["title"] == "Doc B"
    assert patched.json()["data"]["owner"]["name"] == "Member"

    like_add = await client.post(f"/api/v1/documents/{doc_id}/reactions", headers=headers, json={"type": "like"})
    assert like_add.status_code == 200

    like_get = await client.get(f"/api/v1/documents/{doc_id}/reactions", headers=headers)
    assert like_get.status_code == 200
    assert like_get.json()["data"]["likedByMe"] is True

    comment = await client.post(f"/api/v1/documents/{doc_id}/comments", headers=headers, json={"content": "nice"})
    assert comment.status_code == 200
    comment_id = comment.json()["data"]["id"]

    comment_patch = await client.patch(f"/api/v1/comments/{comment_id}", headers=headers, json={"content": "great"})
    assert comment_patch.status_code == 200
    assert comment_patch.json()["data"]["content"] == "great"

    comment_del = await client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert comment_del.status_code == 200

    like_del = await client.delete(f"/api/v1/documents/{doc_id}/reactions", headers=headers)
    assert like_del.status_code == 200


@pytest.mark.anyio
async def test_document_list_pagination_search_sort_smoke(client, db_session):
    create_user(db_session, email="zoe@gap.org", password="pass1234", role=UserRole.member, name="Zoe")
    create_user(db_session, email="aaron@gap.org", password="pass1234", role=UserRole.member, name="Aaron")

    zoe_token = (await login(client, "zoe@gap.org", "pass1234"))["accessToken"]
    aaron_token = (await login(client, "aaron@gap.org", "pass1234"))["accessToken"]

    zoe_headers = auth_header(zoe_token)
    aaron_headers = auth_header(aaron_token)

    first = await client.post(
        "/api/v1/documents",
        headers=zoe_headers,
        json={"title": "Alpha", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "alpha body"}]}], "status": "draft"},
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/documents",
        headers=aaron_headers,
        json={"title": "Beta", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "beta body"}]}], "status": "draft"},
    )
    assert second.status_code == 200

    page1 = await client.get("/api/v1/documents?page=1&pageSize=1&sort=createdAt&order=desc")
    assert page1.status_code == 200
    page1_json = page1.json()
    assert page1_json["meta"]["page"] == 1
    assert page1_json["meta"]["pageSize"] == 1
    assert page1_json["meta"]["total"] == 2
    assert page1_json["meta"]["totalPages"] == 2
    assert page1_json["meta"]["hasNext"] is True
    assert page1_json["meta"]["hasPrev"] is False
    assert page1_json["data"][0]["title"] == "Beta"
    assert "content" not in page1_json["data"][0]

    page2 = await client.get("/api/v1/documents?page=2&pageSize=1&sort=createdAt&order=desc")
    assert page2.status_code == 200
    assert page2.json()["data"][0]["title"] == "Alpha"

    search = await client.get("/api/v1/documents?page=1&pageSize=10&q=alpha&sort=createdAt&order=desc")
    assert search.status_code == 200
    search_json = search.json()
    assert search_json["meta"]["total"] == 1
    assert search_json["data"][0]["title"] == "Alpha"

    author_sorted = await client.get("/api/v1/documents?page=1&pageSize=10&sort=author&order=desc")
    assert author_sorted.status_code == 200
    author_json = author_sorted.json()
    assert [item["ownerName"] for item in author_json["data"]] == ["Aaron", "Zoe"]


@pytest.mark.anyio
async def test_admin_users_role_change_smoke(client, db_session):
    admin1 = create_user(db_session, email="admin1@gap.org", password="pass1234", role=UserRole.admin, name="Admin1")
    admin2 = create_user(db_session, email="admin2@gap.org", password="pass1234", role=UserRole.admin, name="Admin2")
    member = create_user(db_session, email="member2@gap.org", password="pass1234", role=UserRole.member, name="Member2")

    token = (await login(client, "admin1@gap.org", "pass1234"))["accessToken"]
    headers = auth_header(token)

    users = await client.get("/api/v1/admin/users?page=1&pageSize=20", headers=headers)
    assert users.status_code == 200
    assert users.json()["meta"]["total"] == 3

    promote = await client.patch(f"/api/v1/admin/users/{member.id}/role", headers=headers, json={"role": "admin"})
    assert promote.status_code == 200
    assert promote.json()["data"]["role"] == "admin"

    self_demote = await client.patch(f"/api/v1/admin/users/{admin1.id}/role", headers=headers, json={"role": "member"})
    assert self_demote.status_code == 409

    demote_other = await client.patch(f"/api/v1/admin/users/{admin2.id}/role", headers=headers, json={"role": "member"})
    assert demote_other.status_code == 200
    assert demote_other.json()["data"]["role"] == "member"
