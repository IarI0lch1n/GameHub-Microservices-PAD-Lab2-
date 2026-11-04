# GameHub Lab 2 — Defense Scenario

This document is a short practical plan for demonstrating GameHub during the laboratory defense.

The recommended demonstration takes approximately 7–10 minutes.

---

# 1. Before the Defense

Start Docker Desktop.

Make sure RabbitMQ is running:

```powershell
docker start gamehub-rabbitmq
docker ps
```

Expected ports:

```text
5672
15672
```

Start the complete GameHub stack:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run_all.ps1
```

Open these pages before the demonstration:

```text
GameHub UI
http://127.0.0.1:8000/ui/

System status
http://127.0.0.1:8000/services/status

Gateway Swagger
http://127.0.0.1:8000/docs

RabbitMQ
http://localhost:15672

Langfuse
open the GameHub project
```

RabbitMQ local credentials:

```text
gamehub
gamehub_dev
```

---

# 2. Architecture Explanation

Start by explaining:

> GameHub is a Steam-like application implemented using seven independent business microservices and an API Gateway.

Show the architecture diagram from:

```text
docs/ARCHITECTURE.md
```

Mention the seven services:

```text
Auth
User
Catalog
Order
Library
Review
Notification
```

Explain:

> The API Gateway is infrastructure, therefore it is not counted as one of the business microservices.

---

# 3. Database Isolation

Explain:

> Every business service owns its own database. Services are not allowed to directly query another service's database.

Databases:

```text
gamehub_auth
gamehub_users
gamehub_catalog
gamehub_orders
gamehub_library
gamehub_reviews
gamehub_notifications
```

Example:

> Order Service does not read the Catalog database. It asks Catalog Service through HTTP.

---

# 4. Show Service Status

Open:

```text
http://127.0.0.1:8000/services/status
```

Show that all seven services report:

```text
status: ok
```

Explain:

> Every service has `/health` for liveness and `/ready` for dependency readiness.

Mention future Kubernetes use:

```text
/health -> liveness probe
/ready  -> readiness probe
```

---

# 5. Registration Demo

Open:

```text
http://127.0.0.1:8000/ui/
```

Create a new account.

Use a unique email such as:

```text
demo-<timestamp>@example.com
```

Explain what happens:

```text
Browser
  |
  v
Gateway
  |
  v
Auth Service
  |
  | saves user
  v
gamehub_auth
  |
  | publishes user.registered
  v
RabbitMQ
  |
  v
User Service
  |
  v
gamehub_users
```

Important sentence:

> Profile creation is asynchronous. Auth Service does not directly call User Service.

---

# 6. Purchase Demo

From the UI, purchase a game.

Explain the synchronous part first:

```text
Order Service
     |
     | HTTP
     v
Catalog Service
```

Say:

> Order Service needs an immediate answer from Catalog Service to verify that the game exists, is published and to obtain its current price.

Then explain the asynchronous part:

```text
Order Service
     |
     | order.completed
     v
RabbitMQ
     |
     +--------------------+
     |                    |
     v                    v
Library Service    Notification Service
```

Refresh Library.

Show purchased game.

Open Notifications.

Show:

```text
Purchase completed
```

Important sentence:

> Order Service does not directly know about Library or Notification implementation. It only publishes an integration event.

---

# 7. Distributed Tracing Demo

Open Langfuse.

Find the trace corresponding to the purchase.

Show approximately:

```text
api-gateway POST /api/orders
|
+-- HTTP POST order-service
    |
    +-- order-service POST /api/orders
        |
        +-- HTTP GET catalog-service
        |   |
        |   +-- catalog-service GET /internal/games/{id}
        |
        +-- RabbitMQ publish order.completed
            |
            +-- RabbitMQ consume order.completed
            |   Library Service
            |
            +-- RabbitMQ consume order.completed
                Notification Service
```

Explain:

> The same distributed trace continues across synchronous HTTP and asynchronous RabbitMQ communication.

Mention:

```text
X-Request-ID
X-Correlation-ID
X-Langfuse-Trace-ID
```

---

# 8. Review Demo

Open the purchased game in Library.

Open Reviews.

Create a review.

Explain:

```text
Review Service
     |
     +---- HTTP ----> Catalog Service
     |
     +---- review.created
                   |
                   v
                RabbitMQ
                   |
                   v
          Notification Service
```

Then show the new notification.

---

# 9. RabbitMQ Demo

Open:

```text
http://localhost:15672
```

Show:

```text
gamehub.events
```

Show queues:

```text
user-service.user-registered
library-service.order-completed
notification-service.events
```

Then show DLQs:

```text
user-service.user-registered.dlq
library-service.order-completed.dlq
notification-service.events.dlq
```

Explain:

> Consumers use bounded retry. A poison message is attempted three times and then moved to a Dead Letter Queue.

---

# 10. Resilience Explanation

The retry logic is:

```text
Attempt 1
   |
failure
   |
wait
   v
Attempt 2
   |
failure
   |
wait
   v
Attempt 3
   |
failure
   v
DLQ
```

Mention:

- persistent messages;
- durable queues;
- publisher confirms;
- publish retries;
- consumer retries;
- DLQ;
- idempotent consumers.

---

# 11. Testing Demo

Normal tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Explain:

> Normal unit tests do not require live external infrastructure and do not send traces to Langfuse.

Integration test:

```powershell
$env:RUN_INTEGRATION_TESTS="1"

.\.venv\Scripts\python.exe -m pytest `
    tests\integration\test_purchase_flow.py `
    -v

Remove-Item Env:RUN_INTEGRATION_TESTS
```

Explain that it automatically verifies:

```text
Gateway
registration
user.registered event
User profile creation
catalog
purchase
Order -> Catalog HTTP
order.completed
Library
Notification
duplicate purchase protection
```

---

# 12. Expected Questions

## Why use RabbitMQ instead of HTTP everywhere?

Answer:

> HTTP is used when the caller needs an immediate response. RabbitMQ is used for events where the publisher should not depend on every consumer.

Example:

```text
Order -> Catalog = HTTP
Order -> Library = RabbitMQ
```

---

## Why separate databases?

Answer:

> Database ownership prevents tight coupling. A service exposes contracts through APIs and events instead of sharing tables.

---

## Why API Gateway?

Answer:

> It provides one public entry point, request routing, request and correlation context propagation, centralized upstream error handling and UI hosting.

---

## Does the Gateway authenticate users?

Answer:

> The Gateway forwards the Authorization header. Protected services validate the shared JWT token. This avoids trusting the Gateway as the only authentication boundary.

---

## What happens if RabbitMQ sends an event twice?

Answer:

> Consumers are idempotent. They check identifiers such as order ID, auth user ID and event ID before creating data again.

---

## What happens if a consumer always fails?

Answer:

> The message is retried a limited number of times and then stored in a Dead Letter Queue.

---

## Why Langfuse?

Answer:

> It allows one request to be followed across multiple microservices and RabbitMQ consumers using a common distributed trace.

---

## What happens if Catalog Service is unavailable?

Answer:

> Order Service cannot validate the purchase, and the request fails instead of creating an invalid order. The Gateway also translates unreachable upstream services to 503 and timeout conditions to 504.

---

## Is database commit + RabbitMQ publish atomic?

Answer:

> No. This version has publisher retries and confirms, but there is still a small failure window after database commit and before successful message publication. A production version would use the Transactional Outbox Pattern.

This is a good answer because it demonstrates understanding of distributed consistency instead of pretending the limitation does not exist.

---

# 13. Strong Final Summary

A concise final explanation:

> GameHub demonstrates a practical microservice system with seven independently responsible services, database-per-service isolation, synchronous HTTP communication, asynchronous RabbitMQ events, JWT security, API Gateway routing, distributed Langfuse tracing, structured logs, health checks, retry and DLQ resilience, automated tests and a working web UI.

Then mention:

> The current architecture is also prepared for the next laboratory work, where the services can be containerized and deployed to Kubernetes.