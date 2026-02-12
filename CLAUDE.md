# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**薪日 PayDay** is a WeChat mini-program for workers to track their payday dates and moods, with social features for sharing salary experiences. It's a social-entertainment platform centered around the payday emotional node.

### Architecture

This is a monorepo with three main components:

- **backend/** - FastAPI service (Python 3.11+)
- **miniapp/** - WeChat mini-program (uni-app + Vue3)
- **admin-web/** - Web admin dashboard (Vue3 + Element Plus)

The project follows the technical specification in `docs/技术方案_v1.0.md` and sprint planning in `docs/迭代规划_Sprint与任务.md`.

---

## Common Development Commands

### Backend (FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations (required after model changes)
python3 -m alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create first admin user (required before accessing admin panel)
python3 scripts/create_first_admin.py

# Run tests
pytest
```

**Important**: Always run migrations after model changes. The backend uses Alembic for database versioning.

### Admin Web (Vue3)

```bash
cd admin-web

# Install dependencies
npm install

# Development server (proxies /api to backend on port 8000)
npm run dev

# Build for production
npm run build

# Type check
npm run typecheck
```

The admin panel runs on port 5174 and proxies API requests to `http://127.0.0.1:8000`.

### Miniapp (uni-app)

```bash
cd miniapp

# Install dependencies
npm install

# Development (uses uni-app CLI via `unh`)
npm run dev

# Build
npm run build

# Type check
npm run type-check
```

---

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── api/v1/          # API route handlers
│   ├── core/            # Config, database, security, deps
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic layer
│   ├── tasks/           # Celery async tasks
│   └── utils/          # Utility functions
├── alembic/            # Database migrations
├── scripts/            # Utility scripts
└── requirements.txt     # Python dependencies
```

### Key Design Patterns

1. **Service Layer Pattern**: Business logic lives in `app/services/`, API routes in `app/api/v1/` are thin.
2. **Dependency Injection**: Use `app/core/deps.py` for database sessions and current user.
3. **Pydantic Schemas**: All API inputs/outputs use schemas from `app/schemas/`.
4. **SQLAlchemy ORM**: Async sessions via `app/core/database.py`.

### Data Security

- **Salary amounts are encrypted** at rest using `app/utils/encryption.py`
- Never store raw salary values in the database
- Use `encryption_service.encrypt_amount()` and `decrypt_amount()` for salary data

### Authentication

- **Mini-program**: WeChat code2session → JWT (see `app/api/v1/auth.py`)
- **Admin**: Username/password → JWT with `scope=admin` (see `app/core/security.py`)

### Database Migrations

When creating new models or modifying existing ones:

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## Frontend Architecture

### Admin Web

- **Framework**: Vue3 Composition API with TypeScript
- **UI Library**: Element Plus
- **State**: Pinia stores
- **Router**: Vue Router
- **Build**: Vite

Key files:
- `src/api/` - API request modules
- `src/router/` - Route definitions
- `src/stores/` - Pinia state stores
- `src/views/` - Page components

### Miniapp

- **Framework**: uni-app (Vue3) for WeChat mini-program
- **UI**: @dcloudio/uni-ui components
- **State**: Pinia
- **Build**: Vite with uni-app plugins

Key files:
- `src/pages/` - Page components
- `src/components/` - Reusable components
- `src/api/` - API request modules
- `src/stores/` - Pinia state stores
- `src/utils/` - Utility functions

---

## API Design

### Route Structure

- `/api/v1/auth/*` - Authentication (login, token refresh)
- `/api/v1/users/*` - User management
- `/api/v1/payday/*` - Payday configuration
- `/api/v1/salary/*` - Salary records
- `/api/v1/posts/*` - Community posts
- `/api/v1/comments/*` - Comments
- `/api/v1/likes/*` - Likes
- `/api/v1/follows/*` - Follow relationships
- `/api/v1/notifications/*` - User notifications
- `/api/v1/statistics/*` - Statistics and analytics
- `/api/v1/admin/*` - Admin panel endpoints (requires admin scope)

### Authentication Headers

```
Authorization: Bearer <jwt_token>
```

Mini-program tokens have `sub: user_id`, admin tokens have `scope: admin`.

---

## Key Technical Decisions

### Database

- **MySQL 8.0+** as primary database
- **Redis** for caching (user info, payday status, hot posts, session)
- **Planned sharding**: Content tables will be sharded by date/hash for scale

### Async Tasks

- **Celery** with Redis broker for:
  - Risk checking (content moderation)
  - Scheduled notifications (payday reminders)
  - Statistics calculation

### Caching Strategy

- User profile: `user:info:{user_id}` (1h TTL)
- Payday status: `payday:status:{user_id}:{date}` (1d TTL)
- Hot posts: `post:hot:{date}` (Sorted Set, 24h TTL)
- Like status: `like:status:{user_id}:{type}:{id}` (7d TTL)

### Content Moderation

The system implements a multi-layer risk control system (not yet fully implemented):

1. Sensitive word filtering (local)
2. Contact info detection
3. Tencent Cloud YU integration (text/image moderation)
4. OCR for image text extraction
5. Auto-mosaic for sensitive info in salary screenshots

---

## Development Workflow

### Adding a New Feature

1. **Backend**:
   - Create/update model in `app/models/`
   - Generate and apply Alembic migration
   - Create Pydantic schemas in `app/schemas/`
   - Implement service logic in `app/services/`
   - Add API routes in `app/api/v1/`

2. **Frontend**:
   - Create API client in `src/api/`
   - Build UI components
   - Add Pinia store if needed
   - Add route if needed

### Testing Backend

```bash
cd backend
pytest
```

### Code Style

- **Python**: Follow PEP 8, use type hints (mypy strict mode)
- **TypeScript**: Vue3 Composition API style
- **Git Commits**: Use conventional commits format: `feat(scope): description`

---

## Environment Configuration

### Backend

Copy `backend/.env.example` to `backend/.env` and configure:

- `DATABASE_URL` - MySQL connection string
- `REDIS_URL` - Redis connection string
- `WECHAT_APP_ID` - WeChat mini-program AppID
- `WECHAT_APP_SECRET` - WeChat mini-program secret
- `JWT_SECRET_KEY` - JWT signing secret
- `TENCENT_SECRET_ID/KEY` - Tencent Cloud services (optional)

### Frontend

No build-time env vars needed for development. API proxy configured in `vite.config.ts`.

---

## Deployment Notes

1. **Database**: Run migrations before first startup
2. **Admin User**: Create at least one admin user via `scripts/create_first_admin.py`
3. **Celery**: Start worker and beat for async tasks
4. **Proxy**: Configure nginx/proxy for API routing

See `docs/管理后台部署说明.md` for detailed deployment instructions.

---

## Current Sprint Status

As per `docs/迭代规划_Sprint与任务.md`:

- **Phase 1 (MVP)**: Sprint 1.1-1.4 (6-8 weeks)
- Current implementation includes basic models for users, paydays, salaries, posts, comments, likes, follows, notifications
- Admin panel authentication and basic structure in place

Refer to sprint docs for specific task breakdowns and acceptance criteria.
