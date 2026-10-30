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
