# GameHub API

GameHub exposes its public backend API through the API Gateway.

Default Gateway address:

```text
http://127.0.0.1:8000
```

The web interface is available at:

```text
http://127.0.0.1:8000/ui/
```

Swagger documentation for the Gateway:

```text
http://127.0.0.1:8000/docs
```

Each individual FastAPI microservice also exposes its own:

```text
/docs
/redoc
/openapi.json
```

---

# Authentication

Handled by Auth Service.

## Register

```http
POST /api/auth/register
```

Example request:

```json
{
  "email": "player@example.com",
  "password": "StrongPassword123!"
}
```

Creates an Auth user and asynchronously publishes:

```text
user.registered
```

---

## Login

```http
POST /api/auth/login
```

Example:

```json
{
  "email": "player@example.com",
  "password": "StrongPassword123!"
}
```

Returns:

```text
access_token
refresh_token
token_type
expires_in
```

---

## Refresh tokens

```http
POST /api/auth/refresh
```

Example:

```json
{
  "refresh_token": "<token>"
}
```

---

## Current authenticated user

```http
GET /api/auth/me
```

Requires:

```http
Authorization: Bearer <access_token>
```

---

# Users

Handled by User Service.

## Get user profile

```http
GET /api/users/{auth_user_id}
```

Example:

```http
GET /api/users/4
```

User profiles are normally created asynchronously after Auth Service publishes:

```text
user.registered
```

---

# Genres

Handled by Catalog Service.

## List genres

```http
GET /api/genres
```

---

## Create genre

```http
POST /api/genres
```

Requires an authenticated user with:

```text
role = admin
```

Example:

```json
{
  "name": "Strategy"
}
```

---

# Games

Handled by Catalog Service.

## List games

```http
GET /api/games
```

Supported query parameters include:

```text
search
genre
min_price
max_price
published
skip
limit
```

Example:

```http
GET /api/games?published=true&limit=50
```

---

## Get game

```http
GET /api/games/{game_id}
```

Example:

```http
GET /api/games/1
```

---

## Create game

```http
POST /api/games
```

Admin only.

Example:

```json
{
  "title": "Example Game",
  "description": "Game description",
  "price": 29.99,
  "release_date": "2026-11-04",
  "developer": "Example Studio",
  "publisher": "Example Publisher",
  "is_published": true,
  "genre_ids": [1]
}
```

---

## Update game

```http
PATCH /api/games/{game_id}
```

Admin only.

---

## Delete game

```http
DELETE /api/games/{game_id}
```

Admin only.

---

# Orders

Handled by Order Service.

All Order API operations require authentication.

## Purchase game

```http
POST /api/orders
```

Example:

```json
{
  "game_id": 1
}
```

Before completing the purchase, Order Service synchronously requests game information from Catalog Service.

After completing the purchase, Order Service asynchronously publishes:

```text
order.completed
```

Possible relevant responses:

```text
201 Created
404 Game not found
409 Game already purchased
409 Game unavailable for purchase
503 Catalog Service unavailable
```

---

## Purchase history

```http
GET /api/orders
```

---

## Get order

```http
GET /api/orders/{order_id}
```

---

# Library

Handled by Library Service.

Authentication is required.

Library entries are normally created asynchronously after:

```text
order.completed
```

## Get my library

```http
GET /api/library
```

---

## Get owned game

```http
GET /api/library/{game_id}
```

---

# Reviews

Handled by Review Service.

## List reviews

```http
GET /api/games/{game_id}/reviews
```

Public endpoint.

---

## Create review

```http
POST /api/games/{game_id}/reviews
```

Authentication required.

Example:

```json
{
  "rating": 5,
  "content": "Excellent game."
}
```

Rating range:

```text
1–5
```

Review Service synchronously validates the game through Catalog Service.

After successful creation it publishes:

```text
review.created
```

---

## Update own review

```http
PATCH /api/reviews/{review_id}
```

Authentication required.

Users cannot modify another user's review.

---

## Delete own review

```http
DELETE /api/reviews/{review_id}
```

Authentication required.

---

# Notifications

Handled by Notification Service.

Authentication is required.

## List notifications

```http
GET /api/notifications
```

Optional query parameter:

```text
unread_only=true
```

Example:

```http
GET /api/notifications?unread_only=true
```

---

## Mark notification as read

```http
PATCH /api/notifications/{notification_id}/read
```

---

# Infrastructure Endpoints

Every GameHub service provides:

```http
GET /health
GET /ready
```

`/health` is a liveness endpoint.

`/ready` checks whether the service dependencies are available.

The API Gateway additionally provides:

```http
GET /services
GET /services/status
```

The complete system can be checked at:

```text
http://127.0.0.1:8000/services/status
```

---

# Internal Service API

Some endpoints are intended only for service-to-service communication.

Catalog Service provides:

```http
GET /internal/games/{game_id}
```

It is used by:

```text
Order Service
Review Service
```

The API Gateway does not expose `/internal/*` through its public `/api/*` routing.

---

# Authentication Header

Protected endpoints expect:

```http
Authorization: Bearer <access_token>
```

Services validate access tokens locally using the shared JWT configuration.

---

# Request Context

GameHub propagates:

```text
X-Request-ID
X-Correlation-ID
X-Langfuse-Trace-ID
X-Langfuse-Parent-Span-ID
```

These values allow requests to be correlated across multiple microservices.

---

# Common Error Responses

GameHub uses standard HTTP status codes.

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
503 Service Unavailable
504 Gateway Timeout
```

Examples:

```text
401 -> invalid or missing access token
403 -> administrator role required
404 -> game/order/review not found
409 -> duplicate purchase or duplicate review
503 -> required downstream service unavailable
504 -> Gateway upstream timeout
```