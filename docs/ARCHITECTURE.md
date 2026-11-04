# GameHub Architecture

This document describes the internal architecture of GameHub and the main design decisions used for PAD Laboratory Work #2.

---

# 1. Architectural Style

GameHub uses a microservice architecture.

The application consists of:

```text
7 business microservices
1 API Gateway
1 RabbitMQ broker
7 logical SQL Server databases
1 web UI
1 distributed tracing platform
```

Each business service owns one clear domain responsibility.

---

# 2. Complete Architecture

```mermaid
flowchart TB

    Browser[Web Browser]
    UI[GameHub Web UI]
    Gateway[API Gateway :8000]

    Auth[Auth Service :8001]
    User[User Service :8002]
    Catalog[Catalog Service :8003]
    Order[Order Service :8004]
    Library[Library Service :8005]
    Review[Review Service :8006]
    Notification[Notification Service :8007]

    Rabbit[(RabbitMQ<br/>gamehub.events)]

    AuthDB[(gamehub_auth)]
    UserDB[(gamehub_users)]
    CatalogDB[(gamehub_catalog)]
    OrderDB[(gamehub_orders)]
    LibraryDB[(gamehub_library)]
    ReviewDB[(gamehub_reviews)]
    NotificationDB[(gamehub_notifications)]

    Langfuse[Langfuse]

    Browser --> UI
    UI --> Gateway

    Gateway --> Auth
    Gateway --> User
    Gateway --> Catalog
    Gateway --> Order
    Gateway --> Library
    Gateway --> Review
    Gateway --> Notification

    Auth --> AuthDB
    User --> UserDB
    Catalog --> CatalogDB
    Order --> OrderDB
    Library --> LibraryDB
    Review --> ReviewDB
    Notification --> NotificationDB

    Order -->|Synchronous HTTP| Catalog
    Review -->|Synchronous HTTP| Catalog

    Auth -. user.registered .-> Rabbit
    Order -. order.completed .-> Rabbit
    Review -. review.created .-> Rabbit

    Rabbit -. user.registered .-> User
    Rabbit -. order.completed .-> Library
    Rabbit -. order.completed .-> Notification
    Rabbit -. review.created .-> Notification

    Gateway -. traces .-> Langfuse
    Auth -. traces .-> Langfuse
    User -. traces .-> Langfuse
    Catalog -. traces .-> Langfuse
    Order -. traces .-> Langfuse
    Library -. traces .-> Langfuse
    Review -. traces .-> Langfuse
    Notification -. traces .-> Langfuse
```

---

# 3. Service Responsibilities

## Auth Service

Owns:

```text
registration
login
password hashes
access tokens
refresh tokens
roles
```

Publishes:

```text
user.registered
```

Database:

```text
gamehub_auth
```

---

## User Service

Owns:

```text
user profile
display name
profile information
```

Consumes:

```text
user.registered
```

Database:

```text
gamehub_users
```

---

## Catalog Service

Owns:

```text
games
genres
prices
descriptions
publication state
```

Database:

```text
gamehub_catalog
```

Provides an internal endpoint used by other services:

```text
GET /internal/games/{game_id}
```

---

## Order Service

Owns:

```text
purchases
order history
purchase price snapshot
order status
```

Synchronous dependency:

```text
Catalog Service
```

Publishes:

```text
order.completed
```

Database:

```text
gamehub_orders
```

---

## Library Service

Owns:

```text
game ownership
user library
purchase ownership record
```

Consumes:

```text
order.completed
```

Database:

```text
gamehub_library
```

---

## Review Service

Owns:

```text
game ratings
review content
review editing
review deletion
```

Synchronous dependency:

```text
Catalog Service
```

Publishes:

```text
review.created
```

Database:

```text
gamehub_reviews
```

---

## Notification Service

Owns:

```text
user notifications
read/unread state
notification history
```

Consumes:

```text
order.completed
review.created
```

Database:

```text
gamehub_notifications
```

---

# 4. API Gateway

The API Gateway is the only intended public backend entry point.

```text
Client
   |
   v
API Gateway
   |
   +----> service
```

Responsibilities:

- route requests;
- preserve Authorization;
- generate and propagate request context;
- propagate tracing context;
- normalize upstream failures;
- expose aggregate service status;
- serve the web UI.

The Gateway itself does not own business data.

Authentication is still verified by protected business services through the shared JWT validation code.

---

# 5. Database-per-Service

GameHub follows database ownership boundaries.

```text
Auth         -> gamehub_auth
User         -> gamehub_users
Catalog      -> gamehub_catalog
Order        -> gamehub_orders
Library      -> gamehub_library
Review       -> gamehub_reviews
Notification -> gamehub_notifications
```

No service directly reads another service's database.

For example, Order Service cannot query:

```text
gamehub_catalog.games
```

directly.

Instead it performs:

```text
GET Catalog Service /internal/games/{id}
```

This maintains service independence.

---

# 6. Synchronous Communication

Synchronous HTTP is used when the caller needs an immediate result.

## Purchase Example

```text
Client
  |
  v
Gateway
  |
  v
Order Service
  |
  | GET /internal/games/{id}
  v
Catalog Service
```

Order Service needs the current title, price and publication status before creating the order.

Without this response, the order cannot continue.

---

# 7. Asynchronous Communication

RabbitMQ is used when a service should publish a fact without tightly coupling itself to every consumer.

Topic exchange:

```text
gamehub.events
```

## Registration

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

Auth Service does not need to synchronously create a profile in User Service.

---

## Purchase

```text
Order Service
    |
    | order.completed
    v
RabbitMQ
    |
    +-------------------+
    |                   |
    v                   v
Library           Notification
```

Order Service does not need to know how many consumers react to the purchase.

Another consumer could be added later without changing Order Service.

---

# 8. Event Envelope

Integration events use a common structure:

```json
{
  "event_id": "uuid",
  "event_type": "order.completed",
  "occurred_at": "timestamp",
  "correlation_id": "uuid",
  "data": {}
}
```

Distributed tracing may additionally attach:

```json
{
  "_trace": {
    "trace_id": "...",
    "parent_span_id": "..."
  }
}
```

---

# 9. Reliability

RabbitMQ communication uses:

```text
durable exchanges
durable queues
persistent messages
publisher confirms
mandatory publishing
QoS / prefetch
bounded retries
Dead Letter Queues
```

Consumer retry flow:

```text
Attempt 1
   |
   | failure
   v
Retry
   |
Attempt 2
   |
   | failure
   v
Retry
   |
Attempt 3
   |
   | failure
   v
Dead Letter Queue
```

Retry count is propagated using:

```text
x-delivery-attempt
```

---

# 10. Dead Letter Queues

GameHub declares a separate dead-letter exchange:

```text
gamehub.events.dead-letter
```

Examples:

```text
user-service.user-registered.dlq
library-service.order-completed.dlq
notification-service.events.dlq
```

A poison message remains available for inspection instead of being silently lost.

---

# 11. Idempotency

RabbitMQ provides at-least-once style delivery semantics during failures and reconnections.

Therefore consumers must tolerate duplicates.

GameHub performs idempotency checks such as:

```text
User Service:
auth_user_id already exists?

Library Service:
order_id already exists?
user/game ownership already exists?

Notification Service:
source_event_id already exists?
```

Database uniqueness constraints provide an additional protection layer.

---

# 12. Distributed Tracing

GameHub carries tracing context across process boundaries.

HTTP headers:

```text
X-Request-ID
X-Correlation-ID
X-Langfuse-Trace-ID
X-Langfuse-Parent-Span-ID
```

RabbitMQ events carry tracing metadata in `_trace`.

This allows one purchase to appear as one distributed trace:

```text
Gateway request
  |
  v
Gateway -> Order HTTP span
  |
  v
Order request
  |
  +----> Catalog HTTP span
  |          |
  |          v
  |      Catalog request
  |
  +----> RabbitMQ publish
              |
              +----> Library consume
              |
              +----> Notification consume
```

---

# 13. Health and Readiness

Every service exposes:

```text
/health
/ready
```

Liveness:

```text
Is the service process alive?
```

Readiness:

```text
Can the service actually perform its work?
```

Readiness can include:

- database connectivity;
- RabbitMQ connectivity;
- dependent service availability.

The Gateway aggregates status using:

```text
/services/status
```

---

# 14. Error Handling

Examples implemented by GameHub:

```text
400 invalid request
401 authentication required
403 insufficient role
404 entity not found
409 business conflict
503 downstream service unavailable
504 downstream timeout
```

Examples of `409`:

```text
duplicate account
duplicate genre
duplicate purchase
duplicate review
```

---

# 15. Security Boundary

User passwords are never stored in plaintext.

Passwords use Argon2 hashes.

JWT access and refresh tokens have separate token types.

API secrets such as:

```text
JWT_SECRET_KEY
LANGFUSE_SECRET_KEY
database credentials
```

exist only in local environment configuration and are excluded from Git.

---

# 16. Known Trade-Off: Transactional Outbox

Current publisher flow is:

```text
commit business transaction
        |
        v
publish RabbitMQ event
```

There is a small theoretical failure window:

```text
DB commit succeeds
process crashes
event is not published
```

Retries solve publish failures while the process is alive, but they do not make the database commit and message publish one atomic transaction.

A production-grade next step is the Transactional Outbox Pattern:

```text
Business transaction
        |
        +---- business row
        |
        +---- outbox row
               |
               v
        background publisher
               |
               v
           RabbitMQ
```

For Laboratory Work #2 this is documented as a deliberate architectural trade-off.

---

# 17. Future Lab #3 Mapping

The current architecture maps naturally to Kubernetes.

Each service can become:

```text
Deployment
Service
ConfigMap / Secret
```

Existing endpoints:

```text
/health
/ready
```

can become:

```text
livenessProbe
readinessProbe
```

RabbitMQ and SQL Server can later be deployed separately or provided as external infrastructure.