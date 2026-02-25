# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**薪日 PayDay** is a WeChat mini-program for workers to track their payday dates and moods, with social features for sharing salary experiences. It's a social-entertainment platform centered around the payday emotional node.

### Architecture

This is a monorepo with three main components:

- **backend/** - FastAPI service (Python 3.11+, CI uses 3.9+)
- **miniapp/** - WeChat mini-program (uni-app + Vue3)
- **admin-web/** - Web admin dashboard (Vue3 + Element Plus)

The project follows the technical specification in `docs/技术方案_v1.0.md` and sprint planning in `docs/迭代规划_Sprint与任务.md`.

---

## Common Development Commands

### Backend (FastAPI)

\`\`\`bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt  # Includes dev tools (pytest, black, pylint, ruff, etc.)

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

# Test with Vitest UI (interactive)
npm run test:ui

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

# Test with Vitest UI (interactive)
npm run test:ui

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
3. **Pydantic Schemas**: All API inputs/outputs use schemas from \`app/schemas/\` for validation.
4. **SQLAlchemy ORM**: Async sessions via \`app/core/database.py\`.
5. **Exception Handling**: Use custom exceptions from \`app/core/exceptions.py\` (PayDayException, BusinessException, AuthenticationException, etc.) and \`error_response()\` for unified error responses.

### Data Security

- **Salary amounts are encrypted** at rest using \`app/utils/encryption.py\`
- Never store raw salary values in the database
- Use \`encryption_service.encrypt_amount()\` and \`decrypt_amount()\` for salary data

### CSRF Protection

The application implements strict CSRF protection for state-changing operations:

- **Admin endpoints**: All requests to \`/api/v1/admin/*\` require CSRF validation (including GET requests with non-readonly parameters)
- **User endpoints**: POST/PUT/DELETE/PATCH operations require CSRF validation
- **Safe methods**: Standard REST read-only operations (GET, HEAD, OPTIONS) are exempt for user endpoints
- **Implementation**: Use \`verify_csrf_token()\` for admin routes, \`verify_csrf_token_for_user()\` for user routes

Usage in routes:
\`\`\`python
from app.core.deps import verify_csrf_token

@router.delete("/admin/endpoint")
async def endpoint(..., _csrf: bool = Depends(verify_csrf_token)):
    ...
\`\`\`

### Rate Limiting

Built-in rate limiters available as dependencies in \`app/core/deps.py\`:

- \`rate_limit_general()\` - 100 requests/minute for general APIs
- \`rate_limit_login()\` - 5 requests/minute for login endpoints (prevents brute force)
- \`rate_limit_post()\` - 10 requests/minute for posting content
- \`rate_limit_comment()\` - 20 requests/minute for comments

Usage:
\`\`\`python
from app.core.deps import rate_limit_login

@router.post("/auth/login")
async def login(..., _rate_limit: bool = Depends(rate_limit_login)):
    ...
\`\`\`

### Authentication

- **Mini-program**: WeChat code2session → JWT (see \`app/api/v1/auth.py\`)
- **Admin**: Username/password → JWT with \`scope=admin\` (see \`app/core/security.py\`)

### Permission System

Admin roles and hierarchy (defined in \`app/core/deps.py\`):

- \`superadmin\` - Level 3: Full access including user management
- \`admin\` - Level 2: Standard admin operations
- \`readonly\` - Level 1: Read-only access

Usage:
\`\`\`python
from app.core.deps import require_permission

@router.put("/endpoint")
async def endpoint(..., _perm: bool = Depends(require_permission("admin"))):
    ...
\`\`\`

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
- \`src/components/pointShop/\` - Shared components for Point Shop module

### Admin Web Shared Components

The admin panel includes reusable Vue 3 components in \`src/components/pointShop/\`:

- \`CategoryTreeSelect\` - Hierarchical category picker with single selection
- \`CourierSelect\` - Courier company dropdown with feature tags (COD, cold chain)
- \`AddressForm\` - Complete address form with validation (contact, phone, region, detailed address)
- \`RegionPricingForm\` - Shipping pricing configuration by region

Import usage:
\`\`\`typescript
import {
  CategoryTreeSelect,
  CourierSelect,
  AddressForm,
  RegionPricingForm,
  type AddressFormData,
  type RegionPricing,
  type PricingConfig,
} from '@/components/pointShop'
\`\`\`

See \`admin-web/src/components/pointShop/README.md\` for detailed documentation.

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
- **Migrations**: Alembic for database version control

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

# Run integration tests only
pytest tests/integration/ -v

# Run async tests only
pytest -m asyncio

# Run tests matching a keyword expression
pytest -k "test_login" -v
\`\`\`

**Test Markers** (configured in pytest.ini):
- `slow` - Slow running tests (deselect with `-m "not slow"`)
- `integration` - Integration tests (full stack with DB)
- `unit` - Unit tests (isolated, fast)
- `asyncio` - Async tests

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

### CI/CD

GitHub Actions workflow in `.github/workflows/test.yml` runs on push/PR to main/develop:
- Backend tests with coverage (pytest, codecov)
- Miniapp tests with coverage (vitest)
- Admin-web tests with coverage (vitest)
- Integration tests with MySQL + Redis services
- Code quality checks (pylint, black, eslint)

### Running All Tests (Root Level)

\`\`\`bash
# Run all tests (backend + admin + miniapp)
npm run test

# Run all tests with coverage
npm run test:ci

# Run specific component tests
npm run test:backend
npm run test:admin
npm run test:miniapp
\`\`\`

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
   \`\`\`bash
   cd backend && python3 -m alembic upgrade head
   \`\`\`

2. **Admin User**: Create at least one admin user
   \`\`\`bash
   cd backend && python3 scripts/create_first_admin.py
   \`\`\`

3. **Celery** (async tasks and scheduled jobs):
   \`\`\`bash
   cd backend

   # Start Celery worker (executes async tasks)
   celery -A app.celery_app.celery worker -l info

   # Start Celery beat (scheduled tasks like payday reminders)
   celery -A app.celery_app.celery beat -l info

   # Start both with flower monitoring (optional)
   celery -A app.celery_app.celery flower --port=5555
   \`\`\`

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

## Point Shop Admin Module

### Features

The points shop admin module provides comprehensive management for:

- **Categories**: Hierarchical product categories (3 levels)
- **Products**: Product CRUD with multi-specification SKU support
- **Couriers**: Express company management
- **User Addresses**: View and manage user delivery addresses
- **Shipping Templates**: Regional shipping cost configuration
- **Shipments**: Order shipment tracking
- **Returns**: Return request processing

### API Endpoints

- `/api/v1/admin/point-categories/*` - Category management
- `/api/v1/admin/point-products/{id}/skus` - SKU management
- `/api/v1/admin/couriers/*` - Courier management
- `/api/v1/admin/user-addresses/*` - Address management
- `/api/v1/admin/shipping-templates/*` - Shipping templates
- `/api/v1/admin/point-shipments/*` - Shipment management
- `/api/v1/admin/point-returns/*` - Return management

### Frontend Pages

- `/admin/point-categories` - Category management
- `/admin/couriers` - Courier management
- `/admin/user-addresses` - Address management
- `/admin/point-shop` - Product management (enhanced with SKU)
- `/admin/shipping-templates` - Shipping template management
- `/admin/point-shipments` - Shipment management
- `/admin/point-returns` - Return management

### Database Models

New models added:
- `PointCategory` - Product categories
- `PointSpecification` - Product specifications (e.g., Color, Size)
- `PointSpecificationValue` - Specification values (e.g., Red, Blue)
- `PointProductSKU` - Product SKUs with independent inventory/pricing
- `PointReturn` - Return requests

Updated models:
- `PointProduct` - Added `category_id`, `has_sku` fields
- `PointOrder` - Added `sku_id`, `address_id`, `shipment_id` fields

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

Available exception types in \`app/core/exceptions.py\`:

- \`PayDayException\` - Base exception (500 Internal Server Error)
- \`BusinessException\` - Business logic errors (400 Bad Request)
- \`AuthenticationException\` - Authentication failures (401 Unauthorized)
- \`AuthorizationException\` - Permission denied (403 Forbidden)
- \`NotFoundException\` - Resource not found (404 Not Found)
- \`ValidationException\` - Parameter validation errors (422 Unprocessable Entity)
- \`RateLimitException\` - Rate limit exceeded (429 Too Many Requests)
- \`ExternalServiceException\` - External service failures (503 Service Unavailable)

Usage examples:

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

# For consistent success responses
from app.core.exceptions import success_response
return success_response(data={"id": 123}, message="创建成功")
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

1. Start backend: \`cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\`
2. Start Celery worker: \`cd backend && celery -A app.celery_app.celery worker -l info\`
3. Start Celery beat (scheduled tasks): \`cd backend && celery -A app.celery_app.celery beat -l info\`
4. Start admin web: \`cd admin-web && npm run dev\` (runs on port 5174)
