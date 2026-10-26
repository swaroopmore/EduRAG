from jose import jwt

from app.core.config import settings
from tests.conftest import Api


def test_register_and_login(client):
    r = client.post("/auth/register", json={"full_name": "Ada Lovelace", "email": "Ada@Example.com", "password": "analytical-1"})
    assert r.status_code == 201
    # email is normalised, login is case-insensitive
    r = client.post("/auth/login", json={"email": "ada@example.COM", "password": "analytical-1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"
    assert "password" not in me.text


def test_duplicate_email_rejected(client):
    Api(client, "dup@example.com")
    r = client.post("/auth/register", json={"full_name": "Dup", "email": "DUP@example.com", "password": "another-pass-1"})
    assert r.status_code == 400
    assert r.json()["code"] == "email_taken"


def test_weak_password_rejected(client):
    r = client.post("/auth/register", json={"full_name": "Weak", "email": "weak@example.com", "password": "short"})
    assert r.status_code == 422
    assert "8 characters" in r.json()["detail"]


def test_wrong_password_and_unknown_user_look_identical(client):
    Api(client, "real@example.com")
    wrong = client.post("/auth/login", json={"email": "real@example.com", "password": "not-the-password"})
    unknown = client.post("/auth/login", json={"email": "ghost@example.com", "password": "whatever-1"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_missing_and_invalid_tokens_return_401(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    forged = jwt.encode({"sub": "not-a-uuid"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    wrong_key = jwt.encode({"sub": "00000000-0000-0000-0000-000000000000"}, "another-secret", algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {wrong_key}"}).status_code == 401


def test_token_of_deleted_or_inactive_user_rejected(client, alice, db):
    from app.models.user import User

    db.query(User).filter(User.email == "alice@example.com").update({"is_active": False})
    db.commit()
    assert alice.get("/auth/me").status_code == 401
    r = client.post("/auth/login", json={"email": "alice@example.com", "password": alice.password})
    assert r.status_code == 401


def test_update_profile_and_change_password(client, alice):
    r = alice.patch("/auth/me", json={"full_name": "  Alice   Liddell "})
    assert r.status_code == 200 and r.json()["full_name"] == "Alice Liddell"

    bad = alice.post("/auth/change-password", json={"current_password": "wrong-password", "new_password": "brand-new-pass-1"})
    assert bad.status_code == 400 and bad.json()["code"] == "wrong_password"

    ok = alice.post("/auth/change-password", json={"current_password": alice.password, "new_password": "brand-new-pass-1"})
    assert ok.status_code == 200
    assert client.post("/auth/login", json={"email": "alice@example.com", "password": alice.password}).status_code == 401
    assert client.post("/auth/login", json={"email": "alice@example.com", "password": "brand-new-pass-1"}).status_code == 200


def test_login_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_PER_5_MIN", 3)
    Api(client, "limited@example.com")
    codes = [
        client.post("/auth/login", json={"email": "limited@example.com", "password": "wrong-password"}).status_code
        for _ in range(5)
    ]
    assert codes[:2] == [401, 401]  # the earlier successful login in Api() consumed one slot
    assert 429 in codes


def test_legacy_passlib_hashes_still_verify():
    """Users registered before the bcrypt switch must still be able to log in."""
    from passlib.context import CryptContext

    from app.auth.security import verify_password

    legacy = CryptContext(schemes=["bcrypt"]).hash("old-password-1")
    assert verify_password("old-password-1", legacy)
    assert not verify_password("other", legacy)
