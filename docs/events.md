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

