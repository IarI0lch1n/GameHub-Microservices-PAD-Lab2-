# GameHub Integration Events

GameHub uses RabbitMQ for asynchronous communication between microservices.

Main topic exchange:

```text
gamehub.events
```

Dead Letter Exchange:

```text
gamehub.events.dead-letter
```

Messages are persistent and publishing uses RabbitMQ publisher confirms.

---

# Common Event Envelope

All GameHub integration events use a common structure:

```json
{
  "event_id": "uuid",
  "event_type": "event.name",
  "occurred_at": "2026-11-04T12:00:00+00:00",
  "correlation_id": "uuid",
  "data": {}
}
```

Fields:

```text
event_id
    Unique integration event identifier.

event_type
    Routing/event type.

occurred_at
    UTC timestamp when the event was created.

correlation_id
    Connects the event to the originating request.

data
    Event-specific business payload.
```

When distributed tracing is active, GameHub additionally attaches:

```json
{
  "_trace": {
    "trace_id": "32-character trace id",
    "parent_span_id": "16-character span id"
  }
}
```

This allows an asynchronous RabbitMQ consumer to continue the same distributed trace.

---

# user.registered

Producer:

```text
Auth Service
```

Routing key:

```text
user.registered
```

Consumer:

```text
User Service
```

Queue:

```text
user-service.user-registered
```

Flow:

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

Example:

```json
{
  "event_id": "8ab1ae18-b1fc-40c5-a444-f76488a75ecc",
  "event_type": "user.registered",
  "occurred_at": "2026-11-04T12:00:00+00:00",
  "correlation_id": "3a292d26-33de-4adb-b14d-55805546ba41",
  "data": {
    "user_id": 15,
    "email": "player@example.com",
    "role": "user"
  }
}
```

Purpose:

```text
Create the corresponding User Service profile
without requiring Auth Service to synchronously
call User Service.
```

---

# order.completed

Producer:

```text
Order Service
```

Routing key:

```text
order.completed
```

Consumers:

```text
Library Service
Notification Service
```

Queues:

```text
library-service.order-completed
notification-service.events
```

Flow:

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

Example:

```json
{
  "event_id": "518c75fb-e86c-44ec-a632-71e499ac315f",
  "event_type": "order.completed",
  "occurred_at": "2026-11-04T12:00:00+00:00",
  "correlation_id": "5586b183-b3e3-4520-b131-8c81048269e7",
  "data": {
    "order_id": 100,
    "user_id": 15,
    "game_id": 7,
    "game_title": "Example Game",
    "price": "29.99"
  }
}
```

Library Service uses the event to create ownership of the purchased game.

Notification Service uses the same event to create a purchase notification.

Order Service does not need to synchronously contact either consumer.

---

# review.created

Producer:

```text
Review Service
```

Routing key:

```text
review.created
```

Consumer:

```text
Notification Service
```

Queue:

```text
notification-service.events
```

Flow:

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

The event causes Notification Service to create a notification confirming that the review was published.

---

# Queue Bindings

Current bindings:

| Queue | Routing key |
|---|---|
| `user-service.user-registered` | `user.registered` |
| `library-service.order-completed` | `order.completed` |
| `notification-service.events` | `order.completed` |
| `notification-service.events` | `review.created` |

---

# Consumer Reliability

Consumers use bounded retries.

Default maximum:

```text
3 delivery attempts
```

Flow:

```text
Attempt 1
   |
   | processing failure
   v
Retry
   |
Attempt 2
   |
   | processing failure
   v
Retry
   |
Attempt 3
   |
   | processing failure
   v
Dead Letter Queue
```

The current delivery attempt is carried through the RabbitMQ header:

```text
x-delivery-attempt
```

Retry messages may additionally contain:

```text
x-last-error
```

---

# Dead Letter Queues

If all processing attempts fail, the event is published to:

```text
gamehub.events.dead-letter
```

with the consumer queue name as its routing key.

Current DLQs include:

```text
user-service.user-registered.dlq

library-service.order-completed.dlq

notification-service.events.dlq
```

Dead-letter messages include diagnostic headers such as:

```text
x-delivery-attempt
x-original-routing-key
x-failed-queue
x-error
```

DLQ messages are intentionally not automatically consumed.

They remain available for inspection and manual recovery.

---

# Publisher Reliability

Publishers use:

```text
persistent messages
publisher confirms
mandatory publishing
bounded retries
```

Default publisher attempts:

```text
3
```

The retry delay increases with every failed attempt.

---

# Idempotent Consumers

Asynchronous messaging can produce duplicate deliveries during failures or reconnections.

GameHub consumers therefore perform idempotency checks before creating business data.

Examples:

```text
User Service
    checks auth_user_id

Library Service
    checks order_id / ownership

Notification Service
    checks source_event_id
```

This allows the same integration event to be safely delivered more than once.

---

# Distributed Tracing

Trace information is propagated through RabbitMQ.

Example purchase trace:

```text
API Gateway
     |
     v
Order Service
     |
     | RabbitMQ publish
     v
order.completed
     |
     +-----------------------+
     |                       |
     v                       v
Library consume      Notification consume
```

The publisher and both consumers can be displayed inside the same Langfuse trace.

Retry attempts and dead-letter processing are also traced.

---

# Known Consistency Limitation

The current producer workflow is conceptually:

```text
Database commit
      |
      v
RabbitMQ publish
```

Publisher retries protect against normal publish failures while the service remains active.

However, the database transaction and RabbitMQ publication are not one atomic transaction.

A production-grade extension would use the:

```text
Transactional Outbox Pattern
```

This is an acknowledged architectural trade-off for the current laboratory implementation.