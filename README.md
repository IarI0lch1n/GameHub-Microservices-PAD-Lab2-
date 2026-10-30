# GameHub Microservices

GameHub is a Steam-inspired backend application developed for **PAD Laboratory Work #2**.

The main goal of the project is to demonstrate a real microservice architecture with independent business services, synchronous REST communication, asynchronous messaging, authentication, persistence, structured logging, tracing, API documentation, and health checks.

---

## Technology Stack

- **Python 3.10+**
- **FastAPI**
- **Microsoft SQL Server**
- **SQLAlchemy**
- **RabbitMQ**
- **aio-pika**
- **JWT authentication**
- **Langfuse**
- **structlog**
- **HTTPX**
- **Pytest**
- **Docker** � prepared for Laboratory Work #3
- **Kubernetes** � planned for Laboratory Work #3

---

# Architecture

The application contains seven business microservices.

```text
                         Client
                           |
                           v
                    +-------------+
                    | API Gateway |
                    +------+------+
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
 +-----------+       +-----------+       +-----------+
 |   Auth    |       |  Catalog  |       |  Review   |
 |  Service  |       |  Service  |       |  Service  |
 +-----------+       +-----------+       +-----------+
       |                   ^                   |
       |                   | REST              |
       v                   |                   |
 +-----------+             |             +-----------+
 |   User    |             |             |   Order   |
 |  Service  |             +-------------|  Service  |
 +-----------+                           +-----+-----+
                                               |
                                               |
                                           RabbitMQ
                                               |
                              +----------------+----------------+
                              |                                 |
                              v                                 v
                       +-------------+                  +----------------+
                       |   Library   |                  | Notification   |
                       |   Service   |                  |    Service     |
                       +-------------+                  +----------------+

Business Microservices
Auth Service
Responsible for:
- user registration;
- login;
- password hashing;
- JWT access tokens;
- refresh tokens;
- authentication.
Default port:
8001

User Service
Responsible for:
- user profile;
- display name;
- account information;
- profile updates.
Default port:
8002

The service can consume:
user.registered

events from RabbitMQ.
Catalog Service
Responsible for:
- games;
- genres;
- game descriptions;
- prices;
- publication state.
Default port:
8003

Order Service
Responsible for:
- purchasing games;
- order creation;
- purchase history;
- order state.
Default port:
8004

Before an order is created, Order Service communicates synchronously with Catalog Service to validate the game and obtain its current price.

After a successful purchase it publishes:
order.completed

to RabbitMQ.
Library Service
Responsible for:
- purchased games;
- user game library;
- ownership checks.
Default port:
8005

Library Service consumes:
order.completed

events asynchronously.
Review Service
Responsible for:
- game reviews;
- ratings;
- review editing;
- review deletion.
Default port:
8006

Notification Service
Responsible for:
- application notifications;
- purchase notifications;
- notification history;
- read/unread state.
Default port:
8007

It can consume events such as:
order.completed
review.created

from RabbitMQ.
API Gateway
The API Gateway is the public entry point of GameHub.

Default port:
8000

Responsibilities:
- request routing;
- JWT validation;
- request ID generation;
- correlation ID propagation;
- centralized error handling;
- service aggregation.
The API Gateway is not counted as one of the business microservices.
Communication
GameHub demonstrates both required communication approaches.
Synchronous communication
REST API is used when a service needs an immediate response.

Example:
Order Service
      |
      | HTTP
      v
Catalog Service

Order Service requests current game information before completing an order.
Asynchronous communication
RabbitMQ is used for event-driven communication.

Example:
Order Service
      |
      | order.completed
      v
   RabbitMQ
      |
      +------------------+
      |                  |
      v                  v
Library Service    Notification Service

RabbitMQ
Default AMQP endpoint:
localhost:5672

RabbitMQ Management UI:
http://localhost:15672

Default local development credentials:
guest / guest

Production credentials must be provided through environment variables.
Database Architecture
The project uses one Microsoft SQL Server instance during local development.

Each microservice owns its own logical database.
gamehub_auth
gamehub_users
gamehub_catalog
gamehub_orders
gamehub_library
gamehub_reviews
gamehub_notifications

A microservice must not directly access another service's database.

Cross-service data is obtained through REST APIs or asynchronous events.
Authentication
Authentication is based on JWT.

Example token payload:
{
  "sub": "15",
  "role": "user"
}

Supported roles:
user
admin

Observability
GameHub uses two logging levels.
Structured application logging
Every service logs:
timestamp
service
level
request_id
correlation_id
message

Langfuse tracing
Langfuse is used for distributed tracing and observability.

The intention is to trace requests across components such as:
API Gateway
    |
    v
Order Service
    |
    +----> Catalog Service
    |
    +----> RabbitMQ
              |
              +----> Library Service
              |
              +----> Notification Service

Health Checks
Every service exposes:
GET /health
GET /ready

/health verifies that the FastAPI process is alive.

/ready verifies that required infrastructure dependencies are available.

These endpoints will later be used as Kubernetes:
- liveness probes;
- readiness probes.
Initial API Design
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

Configuration
Copy:
.env.example

to:
.env

Real secrets must never be committed.

Important configuration groups:
- Microsoft SQL Server;
- JWT;
- RabbitMQ;
- Langfuse;
- service URLs;
- service ports.
Local Development
Create a virtual environment:
python -m venv .venv

Activate it:
.\.venv\Scripts\Activate.ps1

Install dependencies:
python -m pip install --upgrade pip
pip install -r requirements.txt

Testing
Tests will be implemented using:
pytest
pytest-asyncio

Integration tests are located in:
tests/integration

Laboratory Work #2 Requirements
The project is designed to demonstrate:
- 5-6+ backend microservices;
- separation of responsibilities;
- REST API communication;
- asynchronous messaging;
- persistence;
- authentication and authorization;
- API documentation;
- structured logging;
- error handling;
- configuration management;
- health checks;
- integration testing.
Laboratory Work #3 Preparation
The same project will later be used for Docker and Kubernetes.

Planned additions:
Dockerfile
docker-compose.yml
k8s/

Every microservice will become an independent Docker image and Kubernetes Deployment.
Status
Current stage:
[1] Project architecture
[ ] Shared infrastructure
[ ] Auth Service
[ ] User Service
[ ] Catalog Service
[ ] Order Service
[ ] Library Service
[ ] Review Service
[ ] Notification Service
[ ] API Gateway
[ ] Integration tests
[ ] Documentation

