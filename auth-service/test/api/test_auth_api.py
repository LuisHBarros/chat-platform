import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.infrastructure.database.session import get_db_session
from app.infrastructure.database.models import Base

@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def client(async_db):
    async def _get_test_db():
        yield async_db

    app.dependency_overrides[get_db_session] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    # 1. Register new user
    reg_payload = {
        "email": "realuser@example.com",
        "username": "realuser",
        "password": "SecurePassword123!"
    }
    reg_response = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["email"] == "realuser@example.com"
    assert reg_data["username"] == "realuser"

    # 2. Login with registered user credentials
    login_payload = {
        "identity": "realuser@example.com",
        "password": "SecurePassword123!"
    }
    login_response = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert not token_data["access_token"].startswith("mock_")

    # 3. Attempt login with unregistered account -> MUST FAIL 401
    unreg_login = await client.post("/api/v1/auth/login", json={
        "identity": "unregistered@example.com",
        "password": "Password123!"
    })
    assert unreg_login.status_code == 401

    # 4. Attempt login with wrong password -> MUST FAIL 401
    wrong_pwd_login = await client.post("/api/v1/auth/login", json={
        "identity": "realuser@example.com",
        "password": "WrongPassword!"
    })
    assert wrong_pwd_login.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    # Register & Login
    await client.post("/api/v1/auth/register", json={
        "email": "refreshtest@example.com",
        "username": "refreshtest",
        "password": "Password123!"
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "identity": "refreshtest@example.com",
        "password": "Password123!"
    })
    tokens = login_res.json()

    # Rotate Refresh Token
    refresh_res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
