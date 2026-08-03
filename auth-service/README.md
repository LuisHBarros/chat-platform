# 🔐 Auth Service

A production-ready Authentication and User Management microservice built with **Python 3.14**, **FastAPI**, and **SQLAlchemy (Async)** following **Domain-Driven Design (DDD)** and **Clean Architecture** principles.

---

## 🏗️ Architecture & Clean Layers

The project is structured according to Clean Architecture boundaries to ensure independence of frameworks, databases, and external UI adapters.

```
auth-service/
├── app/
│   ├── domain/                  # Core Business Domain (Framework Agnostic)
│   │   ├── entities/            # User, RefreshToken, VerificationToken, TokenPayload
│   │   ├── object_values/       # Email, Username, Password Value Objects
│   │   ├── exceptions/          # Domain Error Hierarchy
│   │   ├── repositories/        # Protocol Contracts (UserRepository, CacheRepository, etc.)
│   │   └── services/            # Pure Domain Services (AuthenticateUser, RotateRefreshToken, etc.)
│   ├── infrastructure/          # External Technical Adapters
│   │   ├── database/            # SQLAlchemy Models, Async Sessions & Repositories
│   │   └── security/            # Bcrypt Hasher & PyJWT Token Services
│   ├── core/                    # App Configurations, Security Specs & DB Engine
│   ├── schemas/                 # Pydantic Schemas & DTOs for API validation
│   ├── use_cases/               # Application Layer Use Cases & Orchestration
│   └── api/                     # FastAPI Routers & Endpoint Handlers
├── alembic/                     # Database Schema Migrations
├── pyproject.toml               # Dependency Manifest (UV / Hatch)
└── README.md
```

---

## ✨ Features & Business Capabilities

- **User Lifecycle Management**: Registration, activation, deactivation, and email verification.
- **Strict Domain Validation**: Immutable Value Objects (`Email`, `Username`, `Password`) enforcing invariants at instantiation.
- **Secure Authentication**: Dual authentication via Email/Password or Username/Password.
- **Refresh Token Rotation (RTR)**: Single-use refresh tokens with automatic revocation of old tokens upon rotation.
- **Token Blacklisting**: Real-time JWT invalidation via Redis cache during logout.
- **Email Verification & Password Reset**: Secure URL-safe token generation and single-use verification state tracking.

---

## 🛠️ Technology Stack

- **Runtime & Package Manager**: Python 3.14+, [`uv`](https://github.com/astral-sh/uv)
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database & ORM**: PostgreSQL, [SQLAlchemy 2.0 (Async Engine)](https://www.sqlalchemy.org/), [AsyncPG](https://github.com/MagicStack/asyncpg)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Security & Tokens**: `PyJWT`, `Bcrypt`

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.14+
- `uv` installed (`pip install uv` or `curl -sSf https://astral.sh/uv/install.sh | sh`)
- PostgreSQL instance & Redis instance

### 2. Installation & Setup
```bash
# Clone the repository and navigate to auth-service
cd auth-service

# Create virtual environment and sync dependencies using uv
uv sync
```

### 3. Environment Variables
Create a `.env.local` file in the root of `auth-service`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/auth_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. Database Migrations
```bash
# Run database migrations
uv run alembic upgrade head
```

---

## 🧪 Testing Checklist & Roadmap

Use this checklist to implement and verify unit, integration, and E2E test coverage across all layers using `pytest` and `pytest-asyncio`.

### 1. Domain Layer Unit Tests (`tests/unit/domain/`)
- [ ] **Value Objects**:
  - [ ] `Email`: Valid emails pass, invalid formats raise `ValidationError`, normalizes to lowercase.
  - [ ] `Username`: Strings between 3 and 50 characters pass; shorter or longer strings raise `ValidationError`.
  - [ ] `Password`: Empty hash raises `ValidationError`.
- [ ] **Entities**:
  - [ ] `User`: Factory `create()` sets correct initial state (`is_active=True`, `is_verified=False`).
  - [ ] `User`: State transitions (`verify`, `deactivate`, `activate`, `change_password`) produce new immutable instances with updated timestamps.
  - [ ] `RefreshToken`: `is_active(now)` evaluates expiration date and `revoked_at` status accurately.
  - [ ] `VerificationToken`: `is_valid(now)` checks expiration and single-use `used_at` flag.
- [ ] **Domain Services**:
  - [ ] `CreateNewUser`: Prevents duplicate email or username registration.
  - [ ] `AuthenticateUser`: Successfully validates credentials and rejects inactive/unverified accounts.
  - [ ] `RotateRefreshToken` & `RefreshAccessToken`: Correctly revokes used refresh tokens, validates expiration, and issues new pairs.
  - [ ] `LogoutUser`: Adds token JTIs to cache blacklist and marks DB refresh tokens as revoked.
  - [ ] `VerifyUserWithToken` & `ResetPasswordWithToken`: Validates single-use tokens and updates user state.

### 2. Infrastructure Layer Integration Tests (`tests/integration/infrastructure/`)
- [ ] **SqlAlchemyUserRepository**: Test `get_by_id`, `get_by_email`, `get_by_username`, and `save` against a test database.
- [ ] **BcryptHasher**: Verify password hashing and check password matching functionality.
- [ ] **JwtTokenService**: Test JWT creation, payload encoding, expiration, and signature validation.

### 3. API & E2E Endpoint Tests (`tests/e2e/`)
- [ ] `POST /api/v1/auth/register`: Returns 201 Created and user response schema.
- [ ] `POST /api/v1/auth/login`: Returns 200 OK with `access_token` and `refresh_token`.
- [ ] `POST /api/v1/auth/refresh`: Successfully rotates tokens; rejects invalid or revoked refresh tokens.
- [ ] `POST /api/v1/auth/logout`: Revokes token and prevents subsequent access with blacklisted token.
- [ ] `POST /api/v1/auth/verify`: Verifies user with valid token string.
- [ ] `POST /api/v1/auth/reset-password`: Successfully updates user password given a valid reset token.
