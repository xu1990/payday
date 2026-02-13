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

\`\`\`bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt  # Includes dev tools (pytest, black, pylint, etc.)

# Run database migrations (required after model changes)
python3 -m alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create first admin user (required before accessing admin panel)
python3 scripts/create_first_admin.py

# Run tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=html

# Lint and format (from root directory)
cd .. && npm run lint:backend    # Pylint
cd .. && npm run format:backend  # Black + isort
\`\`\`

**Important**: Always run migrations after model changes. The backend uses Alembic for database versioning.

### Admin Web (Vue3)

\`\`\`bash
cd admin-web

# Install dependencies
npm install

# Development server (proxies /api to backend on port 8000)
npm run dev

# Build for production
npm run build

# Type check
npm run type-check

# Lint and format (from root directory)
cd .. && npm run lint:admin    # ESLint
cd .. && npm run format:admin  # Prettier
\`\`\`

The admin panel runs on port 5174 and proxies API requests to `http://127.0.0.1:8000`.

### Miniapp (uni-app)

\`\`\`bash
cd miniapp

# Install dependencies
npm install

# Development (uses uni-app CLI via \`unh\`)
npm run dev

# Build
npm run build

# Type check
npm run type-check

# Lint and format (from root directory)
cd .. && npm run lint:miniapp    # ESLint
cd .. && npm run format:miniapp  # Prettier
\`\`\`

---

## Backend Architecture

### Directory Structure

\`\`\`
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
\`\`\`

### Key Design Patterns

1. **Service Layer Pattern**: Business logic lives in \`app/services/\`, API routes in \`app/api/v1/\` are thin.
2. **Dependency Injection**: Use \`app/core/deps.py\` for database sessions (\`get_db\`) and current user (\`get_current_user\`, \`get_current_admin\`).
3. **Pydantic Schemas**: All API inputs/outputs use schemas from \`app/schemas/\`.
4. **SQLAlchemy ORM**: Async sessions via \`app/core/database.py\`.
5. **Exception Handling**: Use custom exceptions from \`app/core/exceptions.py\` (PayDayException, BusinessException, AuthenticationException, etc.) and \`error_response()\` for unified error responses.

### Data Security

- **Salary amounts are encrypted** at rest using \`app/utils/encryption.py\`
- Never store raw salary values in the database
- Use \`encryption_service.encrypt_amount()\` and \`decrypt_amount()\` for salary data

### Authentication

- **Mini-program**: WeChat code2session → JWT (see \`app/api/v1/auth.py\`)
- **Admin**: Username/password → JWT with \`scope=admin\` (see \`app/core/security.py\`)

### Database Migrations

When creating new models or modifying existing ones:

\`\`\`bash
cd backend

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1
\`\`\`

---

## Frontend Architecture

### Admin Web

- **Framework**: Vue3 Composition API with TypeScript
- **UI Library**: Element Plus
- **State**: Pinia stores
- **Router**: Vue Router
- **Build**: Vite

Key files:
- \`src/api/\` - API request modules
- \`src/router/\` - Route definitions
- \`src/stores/\` - Pinia state stores
- \`src/views/\` - Page components

### Miniapp

- **Framework**: uni-app (Vue3) for WeChat mini-program
- **UI**: @dcloudio/uni-ui components
- **State**: Pinia
- **Build**: Vite with uni-app plugins

Key files:
- \`src/pages/\` - Page components
- \`src/components/\` - Reusable components (LazyImage, Loading, EmptyState)
- \`src/api/\` - API request modules
- \`src/stores/\` - Pinia state stores
- \`src/utils/\` - Utility functions

---

## API Design

### Route Structure

- \`/api/v1/auth/*\` - Authentication (login, token refresh)
- \`/api/v1/users/*\` - User management
- \`/api/v1/payday/*\` - Payday configuration
- \`/api/v1/salary/*\` - Salary records
- \`/api/v1/posts/*\` - Community posts
- \`/api/v1/comments/*\` - Comments
- \`/api/v1/likes/*\` - Likes
- \`/api/v1/follows/*\` - Follow relationships
- \`/api/v1/notifications/*\` - User notifications
- \`/api/v1/statistics/*\` - Statistics and analytics
- \`/api/v1/admin/*\` - Admin panel endpoints (requires admin scope)
- \`/api/v1/admin/config/*\` - Admin configuration (memberships, themes, orders)
- \`/api/v1/payment/*\` - Payment endpoints

### Authentication Headers

\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

Mini-program tokens have \`sub: user_id\`, admin tokens have \`scope: admin\`.

---

## Key Technical Decisions

### Database

- **MySQL 8.0+** as primary database
- **Redis** for caching (user info, payday status, hot posts, session)
- **Planned sharding**: Content tables will be sharded by date/hash for scale

### Async Tasks

- **Celery** with Redis broker for:
  - Risk checking (content moderation) - \`app/tasks/risk_check.py\`
  - Scheduled notifications (payday reminders) - \`app/tasks/scheduled.py\`
  - Statistics calculation

### Caching Strategy

- User profile: \`user:info:{user_id}\` (1h TTL)
- Payday status: \`payday:status:{user_id}:{date}\` (1d TTL)
- Hot posts: \`post:hot:{date}\` (Sorted Set, 24h TTL)
- Like status: \`like:status:{user_id}:{type}:{id}\` (7d TTL)

---

## Development Workflow

### Adding a New Feature

1. **Backend**:
   - Create/update model in \`app/models/\`
   - Generate and apply Alembic migration
   - Create Pydantic schemas in \`app/schemas/\`
   - Implement service logic in \`app/services/\`
   - Add API routes in \`app/api/v1/\`

2. **Frontend**:
   - Create API client in \`src/api/\`
   - Build UI components
   - Add Pinia store if needed
   - Add route if needed

### Testing Backend

\`\`\`bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_specific_file.py

# Run single test function
pytest tests/test_specific_file.py::test_function_name

# Run only unit tests (exclude integration/slow)
pytest -m "not integration and not slow"

# Run async tests only
pytest -m asyncio

# Run tests matching a keyword expression
pytest -k "test_login" -v
\`\`\`

### Code Style

- **Python**: Follow PEP 8, use type hints (mypy strict mode)
- **TypeScript**: Vue3 Composition API style
- **Git Commits**: Use conventional commits format: \`feat(scope): description\`

Root-level scripts for running lint/format across all components:
- \`npm run lint:backend\` - Pylint
- \`npm run lint:admin\` - ESLint (admin-web)
- \`npm run lint:miniapp\` - ESLint (miniapp)
- \`npm run format:backend\` - Black + isort
- \`npm run format:admin\` - Prettier (admin-web)
- \`npm run format:miniapp\` - Prettier (miniapp)

---

## Environment Configuration

### Backend

Copy \`backend/.env.example\` to \`backend/.env\` and configure:

- \`MYSQL_HOST\`, \`MYSQL_PORT\`, \`MYSQL_USER\`, \`MYSQL_PASSWORD\`, \`MYSQL_DATABASE\` - MySQL connection
- \`REDIS_URL\` - Redis connection string
- \`WECHAT_APP_ID\`, \`WECHAT_APP_SECRET\` - WeChat mini-program credentials
- \`WECHAT_MCH_ID\`, \`WECHAT_PAY_API_KEY\`, \`WECHAT_PAY_NOTIFY_URL\` - WeChat Pay (for membership)
- \`JWT_SECRET_KEY\` - JWT signing secret
- \`ENCRYPTION_SECRET_KEY\` - 32-byte key for salary encryption
- \`COS_SECRET_ID\`, \`COS_SECRET_KEY\`, \`COS_REGION\`, \`COS_BUCKET\` - Tencent Cloud COS (image storage)
- \`TENCENT_SECRET_ID\`, \`TENCENT_SECRET_KEY\` - Tencent Cloud YU (content moderation)

### Frontend

No build-time env vars needed for development. API proxy configured in \`vite.config.ts\`.

---

## Deployment Notes

1. **Database**: Run migrations before first startup
2. **Admin User**: Create at least one admin user via \`scripts/create_first_admin.py\`
3. **Celery**:
   - Start worker: \`celery -A app.tasks.worker -l info\`
   - Start beat (for scheduled tasks): \`celery -A app.tasks.beat -l info\`
4. **Proxy**: Configure nginx/proxy for API routing

See \`docs/管理后台部署说明.md\` for detailed deployment instructions.

---

## Sprint Planning

Refer to \`docs/迭代规划_Sprint与任务.md\` for detailed sprint breakdown:

- **Phase 1 (MVP)**: Sprint 1.1-1.4 - Basic features (login, payday, salary, homepage, stats, poster, profile)
- **Phase 2 (Community)**: Sprint 2.1-2.4 - Posts, comments, likes, notifications, risk control
- **Phase 3 (Complete)**: Sprint 3.1-3.5 - Follow, insights, check-in, themes, membership

### Current Implementation Status

**Completed**:
- Sprint 1.1-1.4: Basic MVP features ✅
- Sprint 2.1-2.4: Community features ✅
- Sprint 3.1-3.2: Follow, insights, check-in, themes ✅
- Sprint 3.3-3.5: Membership system (models, payment API, orders) ✅
- Exception handling system (app/core/exceptions.py, error_handler.py) ✅

**Pending / In Progress**:
- Miniapp: Membership purchase flow UI (pending)
- Database migrations for new tables (pending)

---

## Key Implementation Notes

### Dependencies

- **Backend**: See \`requirements.txt\` and \`requirements-dev.txt\` for all dependencies
- **Testing**: Uses pytest with asyncio, coverage, and test markers (via \`requirements-dev.txt\`)

### Project Structure Conventions

- **Models**: All ORM models inherit from \`app.models.base.Base\`
- **Schemas**: Pydantic models for request/response validation
- **Services**: Business logic separated from API routes
- **Tasks**: Celery tasks in \`app/tasks/\` for async operations

### Exception Handling Best Practices

When raising exceptions in services or routes:

\`\`\`python
# For business logic errors
from app.core.exceptions import BusinessException, NotFoundException, ValidationException

# Raise appropriate exceptions
raise NotFoundException("用户不存在")
raise ValidationException("参数格式错误", details={"field": "amount"})
raise BusinessException("该操作不允许", code="OPERATION_NOT_ALLOWED")

# For errors that need to return structured responses
from app.core.exceptions import error_response
return error_response(
    status_code=400,
    message="创建失败",
    code="CREATE_FAILED",
    details={"reason": "..."}
)
\`\`\`

### Adding New API Endpoints

Follow this pattern when adding new endpoints:

1. **Create exceptions** (if needed): Add custom exceptions to \`app/core/exceptions.py\`
2. **Create/Update models**: Add ORM models in \`app/models/\`
3. **Generate migration**: Run \`alembic revision --autogenerate -m "description"\`
4. **Create schemas**: Add Pydantic schemas to \`app/schemas/\`
5. **Implement service**: Add business logic to \`app/services/\`
6. **Add routes**: Create API handlers in \`app/api/v1/\`
7. **Register router**: Import and include router in \`app/main.py\`

---

## Quick Start Guide

### First Time Setup

1. Configure environment variables in \`backend/.env\`
2. Run database migrations: \`python3 -m alembic upgrade head\`
3. Create first admin user: \`python3 scripts/create_first_admin.py\`

### Daily Development

1. Start backend: \`cd backend && uvicorn app.main:app --reload\`
2. Start Celery worker: \`celery -A app.tasks.worker -l info\`
3. Start Celery beat: \`celery -A app.tasks.beat -l info\`
