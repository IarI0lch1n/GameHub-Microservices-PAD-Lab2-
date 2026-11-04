import asyncio
import json

from collections.abc import (
    Awaitable,
    Callable,
)

import aio_pika

from aio_pika import (
    DeliveryMode,
    ExchangeType,
    Message,
)

from shared.config.settings import (
    settings,
)

from shared.logging.setup import (
    get_logger,
)

from shared.tracing.observability import (
    attach_current_trace,
    start_span,
    trace_context_from_event,
)


MessageHandler = Callable[
    [dict],
    Awaitable[None],
]


DELIVERY_ATTEMPT_HEADER = (
    "x-delivery-attempt"
)


def _get_delivery_attempt(
    headers,
) -> int:

    if not headers:
        return 1

    raw_value = headers.get(
        DELIVERY_ATTEMPT_HEADER,
        1,
    )

    try:
        value = int(
            raw_value
        )

    except (
        TypeError,
        ValueError,
    ):
        return 1

    return max(
        value,
        1,
    )


class RabbitMQClient:

    def __init__(
        self,
        *,
        service_name: str,
    ) -> None:

        self.service_name = (
            service_name
        )

        self.connection = None
        self.channel = None
        self.exchange = None

        self.dead_letter_exchange = None

    def _logger(
        self,
    ):

        return get_logger(
            self.service_name
        )

    async def connect(
        self,
    ) -> None:

        if (
            self.connection
            is not None
            and not (
                self.connection
                .is_closed
            )
        ):
            return

        self._logger().info(
            "rabbitmq_connecting",
            host=(
                settings.rabbitmq_host
            ),
            port=(
                settings.rabbitmq_port
            ),
            exchange=(
                settings.rabbitmq_exchange
            ),
        )

        self.connection = (
            await aio_pika.connect_robust(
                host=(
                    settings.rabbitmq_host
                ),
                port=(
                    settings.rabbitmq_port
                ),
                login=(
                    settings
                    .rabbitmq_username
                ),
                password=(
                    settings
                    .rabbitmq_password
                ),
                virtualhost=(
                    settings.rabbitmq_vhost
                ),
            )
        )

        self.channel = (
            await self.connection.channel(
                publisher_confirms=True,
                on_return_raises=True,
            )
        )

        await self.channel.set_qos(
            prefetch_count=10
        )

        self.exchange = (
            await self.channel
            .declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.TOPIC,
                durable=True,
            )
        )

        self.dead_letter_exchange = (
            await self.channel
            .declare_exchange(
                (
                    settings
                    .rabbitmq_dead_letter_exchange
                ),
                ExchangeType.TOPIC,
                durable=True,
            )
        )

        self._logger().info(
            "rabbitmq_connected",
            exchange=(
                settings.rabbitmq_exchange
            ),
            dead_letter_exchange=(
                settings
                .rabbitmq_dead_letter_exchange
            ),
        )

    async def publish(
        self,
        *,
        routing_key: str,
        event: dict,
        headers: (
            dict
            | None
        ) = None,
    ) -> None:

        if (
            self.exchange is None
            or self.channel is None
            or self.channel.is_closed
        ):

            raise RuntimeError(
                (
                    "RabbitMQ publisher "
                    "is not connected."
                )
            )

        with start_span(
            name=(
                "RabbitMQ publish "
                + routing_key
            ),
            input_data={
                "event_id": (
                    event.get(
                        "event_id"
                    )
                ),
                "event_type": (
                    event.get(
                        "event_type"
                    )
                ),
            },
            metadata={
                "service": (
                    self.service_name
                ),
                "exchange": (
                    settings
                    .rabbitmq_exchange
                ),
                "routing_key": (
                    routing_key
                ),
                "correlation_id": (
                    event.get(
                        "correlation_id"
                    )
                ),
            },
        ) as trace_span:

            traced_event = (
                attach_current_trace(
                    event
                )
            )

            body = json.dumps(
                traced_event,
                ensure_ascii=False,
                default=str,
            ).encode(
                "utf-8"
            )

            publish_headers = dict(
                headers
                or {}
            )

            last_error = None

            for attempt in range(
                1,
                (
                    settings
                    .rabbitmq_publish_max_attempts
                    + 1
                ),
            ):

                message = Message(
                    body=body,
                    content_type=(
                        "application/json"
                    ),
                    delivery_mode=(
                        DeliveryMode.PERSISTENT
                    ),
                    message_id=(
                        traced_event.get(
                            "event_id"
                        )
                    ),
                    correlation_id=(
                        traced_event.get(
                            "correlation_id"
                        )
                    ),
                    type=(
                        traced_event.get(
                            "event_type"
                        )
                    ),
                    headers=(
                        publish_headers
                    ),
                )

                try:

                    await self.exchange.publish(
                        message,
                        routing_key=(
                            routing_key
                        ),
                        mandatory=True,
                    )

                    if trace_span is not None:

                        trace_span.update(
                            output={
                                "published": True,
                                "attempt": (
                                    attempt
                                ),
                            }
                        )

                    break

                except Exception as exc:

                    last_error = exc

                    if (
                        attempt
                        >= settings
                        .rabbitmq_publish_max_attempts
                    ):

                        if trace_span is not None:

                            trace_span.update(
                                level="ERROR",
                                status_message=(
                                    str(exc)
                                ),
                            )

                        raise

                    delay = (
                        settings
                        .rabbitmq_publish_retry_delay_seconds
                        * attempt
                    )

                    self._logger().warning(
                        "rabbitmq_publish_retry",
                        event_id=(
                            event.get(
                                "event_id"
                            )
                        ),
                        event_type=(
                            event.get(
                                "event_type"
                            )
                        ),
                        routing_key=(
                            routing_key
                        ),
                        attempt=attempt,
                        next_attempt=(
                            attempt + 1
                        ),
                        delay_seconds=(
                            delay
                        ),
                        error=str(
                            exc
                        ),
                    )

                    await asyncio.sleep(
                        delay
                    )

            if (
                last_error is not None
                and trace_span is not None
            ):

                trace_span.update(
                    metadata={
                        "required_retry": (
                            True
                        )
                    }
                )

        self._logger().info(
            "rabbitmq_event_published",
            event_id=(
                event.get(
                    "event_id"
                )
            ),
            event_type=(
                event.get(
                    "event_type"
                )
            ),
            routing_key=(
                routing_key
            ),
            correlation_id=(
                event.get(
                    "correlation_id"
                )
            ),
        )

    async def _publish_dead_letter(
        self,
        *,
        queue_name: str,
        original_routing_key: str,
        event: dict,
        source_headers: (
            dict
            | None
        ),
        error: Exception,
        delivery_attempt: int,
    ) -> None:

        if self.dead_letter_exchange is None:

            raise RuntimeError(
                (
                    "RabbitMQ dead letter "
                    "exchange is not connected."
                )
            )

        traced_event = (
            attach_current_trace(
                event
            )
        )

        body = json.dumps(
            traced_event,
            ensure_ascii=False,
            default=str,
        ).encode(
            "utf-8"
        )

        headers = dict(
            source_headers
            or {}
        )

        headers[
            DELIVERY_ATTEMPT_HEADER
        ] = delivery_attempt

        headers[
            "x-original-routing-key"
        ] = original_routing_key

        headers[
            "x-failed-queue"
        ] = queue_name

        headers[
            "x-error"
        ] = str(
            error
        )[:500]

        message = Message(
            body=body,
            content_type=(
                "application/json"
            ),
            delivery_mode=(
                DeliveryMode.PERSISTENT
            ),
            message_id=(
                traced_event.get(
                    "event_id"
                )
            ),
            correlation_id=(
                traced_event.get(
                    "correlation_id"
                )
            ),
            type=(
                traced_event.get(
                    "event_type"
                )
            ),
            headers=headers,
        )

        await (
            self.dead_letter_exchange
            .publish(
                message,
                routing_key=(
                    queue_name
                ),
                mandatory=True,
            )
        )

    async def consume(
        self,
        *,
        queue_name: str,
        routing_keys: list[str],
        handler: MessageHandler,
    ) -> None:

        if (
            self.channel is None
            or self.exchange is None
            or self.dead_letter_exchange
            is None
        ):

            raise RuntimeError(
                (
                    "RabbitMQ consumer "
                    "is not connected."
                )
            )

        queue = (
            await self.channel
            .declare_queue(
                queue_name,
                durable=True,
            )
        )

        dead_letter_queue_name = (
            queue_name
            + ".dlq"
        )

        dead_letter_queue = (
            await self.channel
            .declare_queue(
                dead_letter_queue_name,
                durable=True,
            )
        )

        await dead_letter_queue.bind(
            self.dead_letter_exchange,
            routing_key=(
                queue_name
            ),
        )

        for routing_key in routing_keys:

            await queue.bind(
                self.exchange,
                routing_key=(
                    routing_key
                ),
            )

        async def on_message(
            message,
        ) -> None:

            #
            # If our retry/dead-letter publish
            # itself fails, RabbitMQ will requeue
            # the original delivery instead of
            # losing it.
            #

            async with message.process(
                requeue=True
            ):

                try:

                    payload = json.loads(
                        message.body.decode(
                            "utf-8"
                        )
                    )

                except Exception as exc:

                    invalid_event = {
                        "event_id": (
                            message.message_id
                            or "invalid-message"
                        ),
                        "event_type": (
                            message.type
                            or "invalid"
                        ),
                        "correlation_id": (
                            message.correlation_id
                            or ""
                        ),
                        "data": {},
                        "invalid_payload": (
                            message.body.decode(
                                "utf-8",
                                errors="replace",
                            )[:2000]
                        ),
                    }

                    await (
                        self
                        ._publish_dead_letter(
                            queue_name=(
                                queue_name
                            ),
                            original_routing_key=str(
                                message.routing_key
                            ),
                            event=(
                                invalid_event
                            ),
                            source_headers=(
                                message.headers
                            ),
                            error=exc,
                            delivery_attempt=1,
                        )
                    )

                    self._logger().error(
                        (
                            "rabbitmq_invalid_"
                            "message_dead_lettered"
                        ),
                        queue=queue_name,
                        dead_letter_queue=(
                            dead_letter_queue_name
                        ),
                        error=str(
                            exc
                        ),
                    )

                    return

                trace_context = (
                    trace_context_from_event(
                        payload
                    )
                )

                event_type = (
                    payload.get(
                        "event_type"
                    )
                    or "unknown"
                )

                delivery_attempt = (
                    _get_delivery_attempt(
                        message.headers
                    )
                )

                with start_span(
                    name=(
                        "RabbitMQ consume "
                        + str(
                            event_type
                        )
                    ),
                    trace_context=(
                        trace_context
                    ),
                    input_data={
                        "event_id": (
                            payload.get(
                                "event_id"
                            )
                        ),
                        "event_type": (
                            event_type
                        ),
                        "delivery_attempt": (
                            delivery_attempt
                        ),
                    },
                    metadata={
                        "service": (
                            self.service_name
                        ),
                        "queue": (
                            queue_name
                        ),
                        "correlation_id": (
                            payload.get(
                                "correlation_id"
                            )
                        ),
                        "delivery_attempt": (
                            delivery_attempt
                        ),
                    },
                ) as trace_span:

                    self._logger().info(
                        "rabbitmq_event_received",
                        event_id=(
                            payload.get(
                                "event_id"
                            )
                        ),
                        event_type=(
                            event_type
                        ),
                        correlation_id=(
                            payload.get(
                                "correlation_id"
                            )
                        ),
                        queue=queue_name,
                        delivery_attempt=(
                            delivery_attempt
                        ),
                    )

                    try:

                        await handler(
                            payload
                        )

                    except Exception as exc:

                        if (
                            delivery_attempt
                            < settings
                            .rabbitmq_max_delivery_attempts
                        ):

                            next_attempt = (
                                delivery_attempt
                                + 1
                            )

                            delay = (
                                settings
                                .rabbitmq_retry_delay_seconds
                                * delivery_attempt
                            )

                            self._logger().warning(
                                (
                                    "rabbitmq_event_"
                                    "retry_scheduled"
                                ),
                                event_id=(
                                    payload.get(
                                        "event_id"
                                    )
                                ),
                                event_type=(
                                    event_type
                                ),
                                queue=queue_name,
                                current_attempt=(
                                    delivery_attempt
                                ),
                                next_attempt=(
                                    next_attempt
                                ),
                                delay_seconds=(
                                    delay
                                ),
                                error=str(
                                    exc
                                ),
                            )

                            if (
                                trace_span
                                is not None
                            ):

                                trace_span.update(
                                    level="WARNING",
                                    status_message=(
                                        str(exc)
                                    ),
                                    output={
                                        (
                                            "retry_"
                                            "scheduled"
                                        ): True,
                                        "next_attempt": (
                                            next_attempt
                                        ),
                                    },
                                )

                            await asyncio.sleep(
                                delay
                            )

                            retry_headers = dict(
                                message.headers
                                or {}
                            )

                            retry_headers[
                                DELIVERY_ATTEMPT_HEADER
                            ] = next_attempt

                            retry_headers[
                                "x-last-error"
                            ] = str(
                                exc
                            )[:500]

                            await self.publish(
                                routing_key=str(
                                    message.routing_key
                                ),
                                event=payload,
                                headers=(
                                    retry_headers
                                ),
                            )

                            return

                        await (
                            self
                            ._publish_dead_letter(
                                queue_name=(
                                    queue_name
                                ),
                                original_routing_key=str(
                                    message.routing_key
                                ),
                                event=payload,
                                source_headers=(
                                    message.headers
                                ),
                                error=exc,
                                delivery_attempt=(
                                    delivery_attempt
                                ),
                            )
                        )

                        self._logger().error(
                            (
                                "rabbitmq_event_"
                                "dead_lettered"
                            ),
                            event_id=(
                                payload.get(
                                    "event_id"
                                )
                            ),
                            event_type=(
                                event_type
                            ),
                            queue=queue_name,
                            dead_letter_queue=(
                                dead_letter_queue_name
                            ),
                            delivery_attempt=(
                                delivery_attempt
                            ),
                            error=str(
                                exc
                            ),
                        )

                        if (
                            trace_span
                            is not None
                        ):

                            trace_span.update(
                                level="ERROR",
                                status_message=(
                                    str(exc)
                                ),
                                output={
                                    "dead_lettered": (
                                        True
                                    ),
                                    "dead_letter_queue": (
                                        dead_letter_queue_name
                                    ),
                                },
                            )

                        return

                    if trace_span is not None:

                        trace_span.update(
                            output={
                                "processed": True,
                                "delivery_attempt": (
                                    delivery_attempt
                                ),
                            }
                        )

        await queue.consume(
            on_message
        )

        self._logger().info(
            "rabbitmq_consumer_started",
            queue=queue_name,
            dead_letter_queue=(
                dead_letter_queue_name
            ),
            routing_keys=(
                routing_keys
            ),
        )

    async def readiness_check(
        self,
    ) -> dict:

        if (
            self.connection is None
            or self.connection.is_closed
            or self.channel is None
            or self.channel.is_closed
            or self.exchange is None
            or self.dead_letter_exchange
            is None
        ):

            raise RuntimeError(
                (
                    "RabbitMQ connection "
                    "is not ready."
                )
            )

        return {
            "rabbitmq": {
                "status": "ok",
                "host": (
                    settings.rabbitmq_host
                ),
                "port": (
                    settings.rabbitmq_port
                ),
                "exchange": (
                    settings
                    .rabbitmq_exchange
                ),
                "dead_letter_exchange": (
                    settings
                    .rabbitmq_dead_letter_exchange
                ),
            }
        }

    async def close(
        self,
    ) -> None:

        if (
            self.connection is not None
            and not (
                self.connection
                .is_closed
            )
        ):

            await self.connection.close()

        self.connection = None
        self.channel = None
        self.exchange = None
        self.dead_letter_exchange = None

        self._logger().info(
            "rabbitmq_disconnected"
        )