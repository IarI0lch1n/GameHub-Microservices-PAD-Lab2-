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

