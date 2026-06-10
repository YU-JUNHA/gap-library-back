from calendar import monthrange
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.models.document import Document
from app.models.enums import UserRole

from tests.conftest import auth_header, create_user, login


import pytest


KST = ZoneInfo("Asia/Seoul")


def kst_datetime(year: int, month: int, day: int, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=KST)


def set_document_timestamp(db_session, document_id: str, local_dt: datetime) -> None:
    doc = db_session.get(Document, document_id)
    assert doc is not None
    utc_dt = local_dt.astimezone(timezone.utc)
    doc.created_at = utc_dt
    doc.updated_at = utc_dt
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)


async def create_document_at(client, headers, db_session, title: str, local_dt: datetime) -> dict:
    created = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"title": title, "content": [{"type": "paragraph", "content": [{"type": "text", "text": title}]}], "status": "draft"},
    )
    assert created.status_code == 200
    document_id = created.json()["data"]["id"]
    set_document_timestamp(db_session, document_id, local_dt)
    return {"id": document_id, "title": title, "createdAt": local_dt}


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
    member = create_user(db_session, email="member@gap.org", password="pass1234", role=UserRole.member, name="Member")
    member.avatar_url = "https://cdn.example.com/avatar.png"
    db_session.add(member)
    db_session.commit()
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
    assert like_add.json()["data"] == {"likeCount": 1, "likedByMe": True}

    like_add_again = await client.post(f"/api/v1/documents/{doc_id}/reactions", headers=headers, json={"type": "like"})
    assert like_add_again.status_code == 200
    assert like_add_again.json()["data"] == {"likeCount": 1, "likedByMe": True}

    like_get = await client.get(f"/api/v1/documents/{doc_id}/reactions", headers=headers)
    assert like_get.status_code == 200
    assert like_get.json()["data"] == {"likeCount": 1, "likedByMe": True}

    comment = await client.post(f"/api/v1/documents/{doc_id}/comments", headers=headers, json={"content": "nice"})
    assert comment.status_code == 200
    assert comment.json()["data"]["authorName"] == "Member"
    assert comment.json()["data"]["authorAvatarUrl"] == "https://cdn.example.com/avatar.png"
    comment_id = comment.json()["data"]["id"]

    comment_list = await client.get(f"/api/v1/documents/{doc_id}/comments")
    assert comment_list.status_code == 200
    assert comment_list.json()["data"][0]["authorName"] == "Member"
    assert comment_list.json()["data"][0]["authorAvatarUrl"] == "https://cdn.example.com/avatar.png"

    comment_patch = await client.patch(f"/api/v1/comments/{comment_id}", headers=headers, json={"content": "great"})
    assert comment_patch.status_code == 200
    assert comment_patch.json()["data"]["content"] == "great"
    assert comment_patch.json()["data"]["authorName"] == "Member"

    comment_del = await client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert comment_del.status_code == 200

    like_del = await client.delete(f"/api/v1/documents/{doc_id}/reactions", headers=headers)
    assert like_del.status_code == 200
    assert like_del.json()["data"] == {"likeCount": 0, "likedByMe": False}

    like_del_again = await client.delete(f"/api/v1/documents/{doc_id}/reactions", headers=headers)
    assert like_del_again.status_code == 200
    assert like_del_again.json()["data"] == {"likeCount": 0, "likedByMe": False}


@pytest.mark.anyio
async def test_mypage_upload_trend_units_smoke(client, db_session):
    _owner = create_user(db_session, email="owner@gap.org", password="pass1234", role=UserRole.member, name="Owner")
    _other = create_user(db_session, email="other@gap.org", password="pass1234", role=UserRole.member, name="Other")

    owner_token = (await login(client, "owner@gap.org", "pass1234"))["accessToken"]
    other_token = (await login(client, "other@gap.org", "pass1234"))["accessToken"]
    owner_headers = auth_header(owner_token)
    other_headers = auth_header(other_token)

    now_kst = datetime.now(KST)
    today = now_kst.date()
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    month_start = today.replace(day=1)
    month_end_day = monthrange(today.year, today.month)[1]

    owner_docs = []
    for title, local_dt, headers in [
        ("Week Sun", datetime.combine(week_start, time(9, 0), tzinfo=KST), owner_headers),
        ("Week Tue", datetime.combine(week_start + timedelta(days=2), time(10, 0), tzinfo=KST), owner_headers),
        ("Week Sat", datetime.combine(week_start + timedelta(days=6), time(11, 0), tzinfo=KST), owner_headers),
        ("Month 1", kst_datetime(today.year, today.month, 1, 12), owner_headers),
        ("Month 8", kst_datetime(today.year, today.month, 8, 12), owner_headers),
        ("Month 15", kst_datetime(today.year, today.month, 15, 12), owner_headers),
        ("Month 22", kst_datetime(today.year, today.month, 22, 12), owner_headers),
        ("Month 29", kst_datetime(today.year, today.month, min(29, month_end_day), 12), owner_headers),
        ("Year Jan", kst_datetime(today.year, 1, 5, 13), owner_headers),
        ("Year Jun", kst_datetime(today.year, 6, 10, 13), owner_headers),
        ("Year Dec", kst_datetime(today.year, 12, 20, 13), owner_headers),
        ("Other User", kst_datetime(today.year, today.month, 1, 14), other_headers),
    ]:
        result = await create_document_at(client, headers, db_session, title, local_dt)
        if headers is owner_headers:
            owner_docs.append(result)

    expected_by_unit = {}

    def count_docs(predicate):
        return sum(1 for doc in owner_docs if predicate(doc["createdAt"].date()))

    expected_by_unit["week"] = {
        "unit": "week",
        "periodStart": week_start.isoformat(),
        "periodEnd": (week_start + timedelta(days=6)).isoformat(),
        "points": [
            {"label": "일", "count": count_docs(lambda d: d == week_start)},
            {"label": "월", "count": count_docs(lambda d: d == week_start + timedelta(days=1))},
            {"label": "화", "count": count_docs(lambda d: d == week_start + timedelta(days=2))},
            {"label": "수", "count": count_docs(lambda d: d == week_start + timedelta(days=3))},
            {"label": "목", "count": count_docs(lambda d: d == week_start + timedelta(days=4))},
            {"label": "금", "count": count_docs(lambda d: d == week_start + timedelta(days=5))},
            {"label": "토", "count": count_docs(lambda d: d == week_start + timedelta(days=6))},
        ],
    }

    month_points = []
    for label, start_day, end_day in [
        ("1주차", 1, 7),
        ("2주차", 8, 14),
        ("3주차", 15, 21),
        ("4주차", 22, 28),
        ("5주차", 29, month_end_day),
    ]:
        if start_day > month_end_day:
            continue
        count = sum(
            1
            for doc in owner_docs
            if doc["createdAt"].date().year == today.year
            and doc["createdAt"].date().month == today.month
            and start_day <= doc["createdAt"].date().day <= min(end_day, month_end_day)
        )
        month_points.append({"label": label, "count": count})

    expected_by_unit["month"] = {
        "unit": "month",
        "periodStart": month_start.isoformat(),
        "periodEnd": today.replace(day=month_end_day).isoformat(),
        "points": month_points,
    }

    year_points = []
    for month in range(1, 13):
        count = sum(1 for doc in owner_docs if doc["createdAt"].date().year == today.year and doc["createdAt"].date().month == month)
        year_points.append({"label": f"{month}월", "count": count})

    expected_by_unit["year"] = {
        "unit": "year",
        "periodStart": f"{today.year}-01-01",
        "periodEnd": f"{today.year}-12-31",
        "points": year_points,
    }

    total_expected = len(owner_docs)
    latest_owner_doc = max(owner_docs, key=lambda item: item["createdAt"])

    for unit, expected in expected_by_unit.items():
        response = await client.get(f"/api/v1/stats/mypage?unit={unit}", headers=owner_headers)
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["uploadedFileCount"] == total_expected
        assert payload["recentUploads"][0]["documentId"] == latest_owner_doc["id"]
        assert payload["myUploadTrend"]["unit"] == expected["unit"]
        assert payload["myUploadTrend"]["periodStart"] == expected["periodStart"]
        assert payload["myUploadTrend"]["periodEnd"] == expected["periodEnd"]
        assert payload["myUploadTrend"]["points"] == expected["points"]


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
