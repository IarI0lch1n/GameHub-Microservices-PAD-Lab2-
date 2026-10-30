$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "GameHub bootstrap started..." -ForegroundColor Cyan
Write-Host ""

$directories = @(
    "gateway\app",
    "gateway\tests",

    "services\auth-service\app",
    "services\auth-service\tests",

    "services\user-service\app",
    "services\user-service\tests",

    "services\catalog-service\app",
    "services\catalog-service\tests",

    "services\order-service\app",
    "services\order-service\tests",

    "services\library-service\app",
    "services\library-service\tests",

    "services\review-service\app",
    "services\review-service\tests",

    "services\notification-service\app",
    "services\notification-service\tests",

    "shared\config",
    "shared\database",
    "shared\logging",
    "shared\messaging",
    "shared\tracing",

    "infrastructure\mssql",
    "infrastructure\rabbitmq",

    "docs",
    "tests\integration"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$pythonPackages = @(
    "gateway\app",

    "services\auth-service\app",
    "services\user-service\app",
    "services\catalog-service\app",
    "services\order-service\app",
    "services\library-service\app",
    "services\review-service\app",
    "services\notification-service\app",

    "shared",
    "shared\config",
    "shared\database",
    "shared\logging",
    "shared\messaging",
    "shared\tracing"
)

foreach ($package in $pythonPackages) {
    New-Item -ItemType File -Path "$package\__init__.py" -Force | Out-Null
}

$keepDirectories = @(
    "gateway\tests",

    "services\auth-service\tests",
    "services\user-service\tests",
    "services\catalog-service\tests",
    "services\order-service\tests",
    "services\library-service\tests",
    "services\review-service\tests",
    "services\notification-service\tests",

    "infrastructure\mssql",
    "infrastructure\rabbitmq",

    "tests\integration"
)

foreach ($directory in $keepDirectories) {
    New-Item -ItemType File -Path "$directory\.gitkeep" -Force | Out-Null
}


# ============================================================
# .gitignore
# ============================================================

$gitignore = @'
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.so
*.egg-info/
build/
dist/

# Virtual environments
.venv/
venv/
env/
ENV/

# Environment / secrets
.env
.env.local
.env.development
.env.production
.env.test

*.pem
*.key
*.crt

# IDE
.idea/
.vscode/

# Tests / coverage
.pytest_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
.mypy_cache/
.ruff_cache/

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
Desktop.ini

# Local runtime
docker-data/
volumes/

# SQL Server local files
*.mdf
*.ldf
*.ndf

# Temporary
tmp/
temp/
.cache/
'@

Set-Content -Path ".gitignore" -Value $gitignore -Encoding UTF8


# ============================================================
# .env.example
# ============================================================

$envExample = @'
# ============================================================
# GAMEHUB
# ============================================================

APP_ENV=development
LOG_LEVEL=INFO

API_GATEWAY_HOST=127.0.0.1
API_GATEWAY_PORT=8000


# ============================================================
# SERVICE PORTS
# ============================================================

AUTH_SERVICE_PORT=8001
USER_SERVICE_PORT=8002
CATALOG_SERVICE_PORT=8003
ORDER_SERVICE_PORT=8004
LIBRARY_SERVICE_PORT=8005
REVIEW_SERVICE_PORT=8006
NOTIFICATION_SERVICE_PORT=8007


# ============================================================
# SERVICE URLS
# ============================================================

AUTH_SERVICE_URL=http://127.0.0.1:8001
USER_SERVICE_URL=http://127.0.0.1:8002
CATALOG_SERVICE_URL=http://127.0.0.1:8003
ORDER_SERVICE_URL=http://127.0.0.1:8004
LIBRARY_SERVICE_URL=http://127.0.0.1:8005
REVIEW_SERVICE_URL=http://127.0.0.1:8006
NOTIFICATION_SERVICE_URL=http://127.0.0.1:8007


# ============================================================
# MICROSOFT SQL SERVER
# ============================================================

MSSQL_SERVER=localhost
MSSQL_PORT=1433
MSSQL_DRIVER=ODBC Driver 17 for SQL Server

MSSQL_TRUSTED_CONNECTION=true
MSSQL_USERNAME=
MSSQL_PASSWORD=
MSSQL_TRUST_SERVER_CERTIFICATE=true

AUTH_DB_NAME=gamehub_auth
USER_DB_NAME=gamehub_users
CATALOG_DB_NAME=gamehub_catalog
ORDER_DB_NAME=gamehub_orders
LIBRARY_DB_NAME=gamehub_library
REVIEW_DB_NAME=gamehub_reviews
NOTIFICATION_DB_NAME=gamehub_notifications


# ============================================================
# JWT
# ============================================================

JWT_SECRET_KEY=change-me-in-local-env
JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7


# ============================================================
# RABBITMQ
# ============================================================

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

RABBITMQ_EXCHANGE=gamehub.events

RABBITMQ_MANAGEMENT_URL=http://localhost:15672

EVENT_USER_REGISTERED=user.registered
EVENT_ORDER_COMPLETED=order.completed
EVENT_REVIEW_CREATED=review.created


# ============================================================
# LANGFUSE
# ============================================================

LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_ENVIRONMENT=development


# ============================================================
# HTTP / TRACING
# ============================================================

HTTP_TIMEOUT_SECONDS=10

REQUEST_ID_HEADER=X-Request-ID
CORRELATION_ID_HEADER=X-Correlation-ID
'@

Set-Content -Path ".env.example" -Value $envExample -Encoding UTF8

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}


# ============================================================
# requirements.txt
# ============================================================

$requirements = @'
fastapi>=0.115
uvicorn[standard]>=0.32

pydantic>=2.9
pydantic-settings>=2.6
python-dotenv>=1.0

sqlalchemy>=2.0
pyodbc>=5.2

PyJWT>=2.10
passlib[bcrypt]>=1.7
bcrypt>=4.2

httpx>=0.27

aio-pika>=9.5

structlog>=24.4

langfuse>=4

pytest>=8.3
pytest-asyncio>=0.24
'@

Set-Content -Path "requirements.txt" -Value $requirements -Encoding UTF8


# ============================================================
# docs/architecture.md
# ============================================================

$architecture = @'
# GameHub Architecture

GameHub is a Steam-inspired backend built using a microservice architecture.

## Business Services

The project contains seven independent business microservices:

- Auth Service
- User Service
- Catalog Service
- Order Service
- Library Service
- Review Service
- Notification Service

The API Gateway is an infrastructure component and is not counted as a business microservice.

## Core Architecture Rules

1. Every microservice owns its own data.
2. Services must not directly access another service's database.
3. Synchronous communication is performed through REST HTTP APIs.
4. Asynchronous communication is performed through RabbitMQ.
5. Request IDs and correlation IDs are propagated between services.
6. Secrets are supplied through environment variables.
7. Every backend service exposes `/health` and `/ready`.
8. Every FastAPI service provides OpenAPI documentation.

## Purchase Flow

```text
Client
  |
  v
API Gateway
  |
  v
Order Service
  |
  | REST
  v
Catalog Service
  |
  v
Order Service
  |
  | order.completed
  v
RabbitMQ
  |
  +---------> Library Service
  |
  +---------> Notification Service

  Order Service synchronously validates a game through Catalog Service.

After a successful purchase, Order Service publishes an order.completed event.

Library Service and Notification Service process this event asynchronously.
'@

Set-Content -Path "docs\architecture.md" -Value $architecture -Encoding UTF8
# ============================================================

# ============================================================
$events = @'
GameHub Events
GameHub uses RabbitMQ for asynchronous communication.

Main exchange:
gamehub.events

user.registered
Producer:
auth-service

Consumers:
user-service
notification-service

Example:
{
  "event_id": "uuid",
  "event_type": "user.registered",
  "occurred_at": "2026-10-30T10:00:00Z",
  "correlation_id": "uuid",
  "data": {
    "user_id": 15,
    "email": "user@example.com"
  }
}

order.completed
Producer:
order-service

Consumers:
library-service
notification-service

Example:
{
  "event_id": "uuid",
  "event_type": "order.completed",
  "occurred_at": "2026-10-30T10:00:00Z",
  "correlation_id": "uuid",
  "data": {
    "order_id": 100,
    "user_id": 15,
    "game_id": 7,
    "price": 29.99
  }
}

review.created
Producer:
review-service

Consumer:
notification-service

'@

Set-Content -Path "docs\events.md" -Value $events -Encoding UTF8
# ============================================================

# ============================================================
$api = @'
GameHub API
All public requests will eventually pass through the API Gateway.
Authentication
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh

Users
GET   /api/users/me
PATCH /api/users/me

Catalog
GET    /api/games
GET    /api/games/{game_id}
POST   /api/games
PATCH  /api/games/{game_id}
DELETE /api/games/{game_id}

Orders
POST /api/orders
GET  /api/orders
GET  /api/orders/{order_id}

Library
GET /api/library
GET /api/library/{game_id}

Reviews
GET    /api/games/{game_id}/reviews
POST   /api/games/{game_id}/reviews
PATCH  /api/reviews/{review_id}
DELETE /api/reviews/{review_id}

Notifications
GET   /api/notifications
PATCH /api/notifications/{notification_id}/read

Infrastructure
Every service provides:
GET /health
GET /ready

FastAPI Swagger:
/docs

OpenAPI:
/openapi.json

'@

Set-Content -Path "docs\api.md" -Value $api -Encoding UTF8

Write-Host ""
Write-Host "GameHub bootstrap completed successfully." -ForegroundColor Green
Write-Host ""

Write-Host "Root files:" -ForegroundColor Cyan
Get-ChildItem -File -Force

Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Get-ChildItem ".\docs" -File -Force

Write-Host ""
Write-Host "Git status:" -ForegroundColor Cyan
git status --short

