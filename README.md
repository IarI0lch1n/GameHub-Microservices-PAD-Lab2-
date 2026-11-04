# GameHub Microservices

GameHub is a Steam-inspired microservice application developed for **PAD Laboratory Work #2**.

The project demonstrates a complete backend microservice architecture with:

- seven independent business microservices;
- API Gateway;
- synchronous HTTP communication;
- asynchronous RabbitMQ events;
- independent persistence;
- JWT authentication and authorization;
- distributed tracing;
- structured logging;
- retries and Dead Letter Queues;
- health and readiness checks;
- unit and integration testing;
- a web interface for demonstration and normal application use.

---

## Technology Stack

### Backend

- Python 3.10
- FastAPI
- SQLAlchemy
- Microsoft SQL Server
- pyodbc
- HTTPX

### Messaging

- RabbitMQ
- aio-pika
- topic exchanges
- persistent messages
- publisher confirms
- retries
- Dead Letter Queues

### Authentication

- JWT access tokens
- JWT refresh tokens
- Argon2 password hashing
- user/admin roles

### Observability

- structlog
- request IDs
- correlation IDs
- Langfuse
- OpenTelemetry-based distributed tracing

### Testing

- pytest
- pytest-asyncio
- integration tests

### UI

- HTML
- CSS
- JavaScript
- served directly by the API Gateway

---

# System Architecture

GameHub contains **seven business microservices** and one API Gateway.

```mermaid
flowchart TB

    UI[GameHub Web UI]
    GW[API Gateway :8000]

    AUTH[Auth Service :8001]
    USER[User Service :8002]
    CAT[Catalog Service :8003]
    ORDER[Order Service :8004]
    LIB[Library Service :8005]
    REVIEW[Review Service :8006]
    NOTIFY[Notification Service :8007]

    RMQ[(RabbitMQ)]

    DB_AUTH[(gamehub_auth)]
    DB_USER[(gamehub_users)]
    DB_CAT[(gamehub_catalog)]
    DB_ORDER[(gamehub_orders)]
    DB_LIB[(gamehub_library)]
    DB_REVIEW[(gamehub_reviews)]
    DB_NOTIFY[(gamehub_notifications)]

    UI --> GW

    GW --> AUTH
    GW --> USER
    GW --> CAT
    GW --> ORDER
    GW --> LIB
    GW --> REVIEW
    GW --> NOTIFY

    AUTH --> DB_AUTH
    USER --> DB_USER
    CAT --> DB_CAT
    ORDER --> DB_ORDER
    LIB --> DB_LIB
    REVIEW --> DB_REVIEW
    NOTIFY --> DB_NOTIFY

    ORDER -->|HTTP game lookup| CAT
    REVIEW -->|HTTP game lookup| CAT

    AUTH -. user.registered .-> RMQ
    ORDER -. order.completed .-> RMQ
    REVIEW -. review.created .-> RMQ

    RMQ -. user.registered .-> USER
    RMQ -. order.completed .-> LIB
    RMQ -. order.completed .-> NOTIFY
    RMQ -. review.created .-> NOTIFY
```

More architecture details are available in:

```text
docs/ARCHITECTURE.md
```

---

# Services

| Service | Port | Database | Responsibility |
|---|---:|---|---|
| API Gateway | 8000 | — | Public entry point and request routing |
| Auth Service | 8001 | `gamehub_auth` | Registration, login, JWT |
| User Service | 8002 | `gamehub_users` | User profiles |
| Catalog Service | 8003 | `gamehub_catalog` | Games and genres |
| Order Service | 8004 | `gamehub_orders` | Purchases and order history |
| Library Service | 8005 | `gamehub_library` | Purchased game ownership |
| Review Service | 8006 | `gamehub_reviews` | Ratings and reviews |
| Notification Service | 8007 | `gamehub_notifications` | User notifications |

The API Gateway is infrastructure and is **not counted as a business microservice**.

---

# Database Ownership

All services use the same Microsoft SQL Server instance during local development, but each service owns a separate logical database.

```text
gamehub_auth
gamehub_users
gamehub_catalog
gamehub_orders
gamehub_library
gamehub_reviews
gamehub_notifications
```

A service never directly queries another service's database.

Cross-service data is obtained through:

- HTTP APIs;
- RabbitMQ integration events.

---

# Communication

GameHub demonstrates both synchronous and asynchronous communication.

## Synchronous HTTP

Order Service obtains game information from Catalog Service before creating a purchase:

```text
Order Service
     |
     | HTTP GET /internal/games/{id}
     v
Catalog Service
```

Review Service also queries Catalog Service when a review is created.

```text
Review Service
     |
     | HTTP
     v
Catalog Service
```

---

## Asynchronous RabbitMQ

RabbitMQ uses the topic exchange:

```text
gamehub.events
```

### `user.registered`

```text
Auth Service
     |
     | user.registered
     v
RabbitMQ
     |
     v
User Service
```

### `order.completed`

```text
Order Service
     |
     | order.completed
     v
RabbitMQ
     |
     +----------------------+
     |                      |
     v                      v
Library Service    Notification Service
```

### `review.created`

```text
Review Service
     |
     | review.created
     v
RabbitMQ
     |
     v
Notification Service
```

---

# RabbitMQ Reliability

RabbitMQ messages are persistent and publishers use publisher confirms.

The application also implements bounded retries.

Default configuration:

```text
Maximum consumer attempts: 3
Retry delay:                1s, then 2s
Publisher attempts:         3
```

If a consumer cannot process a message after all attempts, the message is sent to a Dead Letter Queue.

Examples:

```text
user-service.user-registered.dlq
library-service.order-completed.dlq
notification-service.events.dlq
```

Dead letter exchange:

```text
gamehub.events.dead-letter
```

This prevents poison messages from producing an infinite requeue loop.

Consumers are designed to be idempotent so duplicate delivery does not create duplicate business records.

---

# Authentication

Authentication is handled by Auth Service.

Supported operations:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
GET  /api/auth/me
```

JWT tokens contain information such as:

```json
{
  "sub": "4",
  "role": "user",
  "type": "access"
}
```

Supported roles:

```text
user
admin
```

Protected API endpoints expect:

```http
Authorization: Bearer <access-token>
```

---

# API Gateway

The API Gateway is available at:

```text
http://127.0.0.1:8000
```

Routing:

```text
/api/auth/*               -> Auth Service
/api/users/*              -> User Service
/api/games/*              -> Catalog Service
/api/genres/*             -> Catalog Service
/api/orders/*             -> Order Service
/api/library/*            -> Library Service
/api/games/{id}/reviews   -> Review Service
/api/reviews/*            -> Review Service
/api/notifications/*      -> Notification Service
```

The Gateway propagates:

```text
Authorization
X-Request-ID
X-Correlation-ID
X-Langfuse-Trace-ID
X-Langfuse-Parent-Span-ID
```

Gateway error handling includes:

```text
503 Service Unavailable
504 Gateway Timeout
```

---

# Web Interface

The GameHub UI is served directly by the API Gateway.

Open:

```text
http://127.0.0.1:8000/ui/
```

The UI supports:

- registration;
- login;
- automatic token refresh;
- catalog browsing;
- game purchasing;
- library;
- order history;
- reviews;
- notifications;
- service status;
- admin game and genre creation.

The UI communicates only through the API Gateway.

It does not directly call individual microservices.

---

# Distributed Tracing

GameHub uses Langfuse for distributed tracing.

Every request receives:

```text
X-Request-ID
X-Correlation-ID
```

Distributed tracing context is propagated through HTTP and RabbitMQ.

A complete purchase trace looks like:

```text
API Gateway
    |
    v
Order Service
    |
    +---- HTTP ----> Catalog Service
    |
    +---- RabbitMQ publish order.completed
                    |
                    +----> Library Service
                    |
                    +----> Notification Service
```

All of these operations can appear inside the same Langfuse trace.

RabbitMQ retry attempts and failed messages are also represented in tracing.

Example poison-message trace:

```text
delivery_attempt=1
        |
        v
retry
        |
delivery_attempt=2
        |
        v
retry
        |
delivery_attempt=3
        |
        v
Dead Letter Queue
```

---

# Structured Logging

All services use structured JSON logging.

Important fields include:

```text
timestamp
service
level
request_id
correlation_id
message
```

Example events:

```text
request_started
request_completed
rabbitmq_event_published
rabbitmq_event_received
rabbitmq_event_retry_scheduled
rabbitmq_event_dead_lettered
order_completed
notification_created
```

---

# Health Checks

Every service exposes:

```text
GET /health
GET /ready
```

`/health` verifies that the process is alive.

`/ready` verifies required dependencies such as:

- database;
- RabbitMQ;
- dependent HTTP services.

The API Gateway can check the complete system:

```text
GET /services/status
```

Example:

```text
http://127.0.0.1:8000/services/status
```

These health endpoints are also suitable for future Kubernetes liveness and readiness probes.

---

# API Documentation

Each FastAPI service provides Swagger/OpenAPI documentation.

Gateway:

```text
http://127.0.0.1:8000/docs
```

Individual services:

```text
http://127.0.0.1:8001/docs
http://127.0.0.1:8002/docs
http://127.0.0.1:8003/docs
http://127.0.0.1:8004/docs
http://127.0.0.1:8005/docs
http://127.0.0.1:8006/docs
http://127.0.0.1:8007/docs
```

---

# Local Requirements

Install:

- Python 3.10+
- Microsoft SQL Server
- Microsoft ODBC Driver 17 for SQL Server
- Docker Desktop
- Git

Check that Python can see the ODBC driver:

```powershell
.\.venv\Scripts\python.exe -c "import pyodbc; print(pyodbc.drivers())"
```

Expected list should contain:

```text
ODBC Driver 17 for SQL Server
```

---

# Installation

Clone the repository:

```powershell
git clone https://github.com/IarI0lch1n/GameHub-Microservices-PAD-Lab2-.git
cd GameHub-Microservices-PAD-Lab2-
```

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create local configuration:

```powershell
Copy-Item .env.example .env
```

Update `.env` with the local SQL Server configuration.

Example:

```env
MSSQL_SERVER=localhost
MSSQL_PORT=1433
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
MSSQL_TRUSTED_CONNECTION=true
```

Real secrets must never be committed.

---

# RabbitMQ

Create the local RabbitMQ container once:

```powershell
docker run -d `
    --name gamehub-rabbitmq `
    -p 5672:5672 `
    -p 15672:15672 `
    -e RABBITMQ_DEFAULT_USER=gamehub `
    -e RABBITMQ_DEFAULT_PASS=gamehub_dev `
    -v gamehub_rabbitmq_data:/var/lib/rabbitmq `
    rabbitmq:4-management
```

For later use:

```powershell
docker start gamehub-rabbitmq
```

Check:

```powershell
docker ps
```

RabbitMQ Management UI:

```text
http://localhost:15672
```

Local development credentials:

```text
Username: gamehub
Password: gamehub_dev
```

---

# Langfuse

Langfuse is optional for basic runtime operation but required to demonstrate distributed tracing.

Configure local `.env`:

```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_ENVIRONMENT=development
```

The keys must never be committed.

The project uses Langfuse Python SDK v4 because the project currently runs on Python 3.10.

---

# Running GameHub

Start RabbitMQ:

```powershell
docker start gamehub-rabbitmq
```

Then launch all seven services and the API Gateway:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run_all.ps1
```

The script starts:

```text
8001 Auth Service
8002 User Service
8003 Catalog Service
8004 Order Service
8005 Library Service
8006 Review Service
8007 Notification Service
8000 API Gateway
```

Check the complete system:

```text
http://127.0.0.1:8000/services/status
```

Open the application:

```text
http://127.0.0.1:8000/ui/
```

---

# Testing

## Unit Tests

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Integration tests are skipped during the normal test suite because they require the complete running infrastructure.

---

## Integration Test

First start the complete GameHub stack.

Then:

```powershell
$env:RUN_INTEGRATION_TESTS="1"

.\.venv\Scripts\python.exe -m pytest `
    tests\integration\test_purchase_flow.py `
    -v

Remove-Item Env:RUN_INTEGRATION_TESTS
```

The integration test verifies:

```text
API Gateway availability
        |
        v
Registration
        |
        v
user.registered
        |
        v
User profile creation
        |
        v
Catalog lookup
        |
        v
Purchase
        |
        +---- HTTP ----> Catalog
        |
        v
order.completed
        |
        +----> Library
        |
        +----> Notification
        |
        v
Duplicate purchase -> 409
```

---

# Important API Endpoints

## Authentication

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
GET  /api/auth/me
```

## Users

```text
GET /api/users/{auth_user_id}
```

## Catalog

```text
GET    /api/genres
POST   /api/genres

GET    /api/games
GET    /api/games/{game_id}
POST   /api/games
PATCH  /api/games/{game_id}
DELETE /api/games/{game_id}
```

## Orders

```text
POST /api/orders
GET  /api/orders
GET  /api/orders/{order_id}
```

## Library

```text
GET /api/library
GET /api/library/{game_id}
```

## Reviews

```text
GET    /api/games/{game_id}/reviews
POST   /api/games/{game_id}/reviews
PATCH  /api/reviews/{review_id}
DELETE /api/reviews/{review_id}
```

## Notifications

```text
GET   /api/notifications
PATCH /api/notifications/{notification_id}/read
```

---

# Resilience and Error Handling

The project demonstrates:

- HTTP timeouts;
- `503 Service Unavailable`;
- `504 Gateway Timeout`;
- publisher confirms;
- publisher retries;
- bounded consumer retries;
- Dead Letter Queues;
- persistent RabbitMQ messages;
- idempotent event consumers;
- duplicate purchase protection;
- database uniqueness constraints.

One known distributed consistency trade-off remains:

```text
Database commit
     |
     v
RabbitMQ publish
```

A process failure between these operations could theoretically leave committed data without its corresponding integration event.

A production-grade extension would use the **Transactional Outbox Pattern**.

This is intentionally documented as a future architectural improvement rather than hidden.

---

# Laboratory Work #2 Coverage

The project demonstrates:

- 5–6+ independent backend microservices;
- seven business microservices;
- separation of responsibilities;
- synchronous service-to-service communication;
- asynchronous message-based communication;
- persistence;
- authentication and authorization;
- API documentation;
- structured logging;
- distributed tracing;
- error handling;
- health and readiness endpoints;
- retries and DLQ;
- integration testing;
- meaningful Git history;
- working UI.

---

# Laboratory Work #3 Preparation

The architecture is designed so that each service can later become an independent Docker image and Kubernetes Deployment.

Possible Lab #3 additions:

```text
Dockerfile
docker-compose.yml
k8s/
```

The existing:

```text
/health
/ready
```

endpoints can be reused as Kubernetes liveness and readiness probes.

---

# Project Status

```text
[x] Architecture
[x] Shared infrastructure
[x] Auth Service
[x] User Service
[x] Catalog Service
[x] Order Service
[x] Library Service
[x] Review Service
[x] Notification Service
[x] API Gateway
[x] Microsoft SQL Server persistence
[x] RabbitMQ messaging
[x] JWT authentication
[x] Structured logging
[x] Langfuse distributed tracing
[x] Publisher retry
[x] Consumer retry
[x] Dead Letter Queues
[x] Unit tests
[x] Integration tests
[x] Web UI
[x] Documentation
```

GameHub Laboratory Work #2 is functionally complete.