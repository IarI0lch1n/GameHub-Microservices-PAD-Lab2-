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

        self._logger().info(
            "rabbitmq_connected",
            exchange=(
                settings.rabbitmq_exchange
            ),
        )

    async def publish(
        self,
        *,
        routing_key: str,
        event: dict,
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
            )

            try:

                await self.exchange.publish(
                    message,
                    routing_key=(
                        routing_key
                    ),
                    mandatory=True,
                )

            except Exception as exc:

                if trace_span is not None:

                    trace_span.update(
                        level="ERROR",
                        status_message=str(
                            exc
                        ),
                    )

                raise

            if trace_span is not None:

                trace_span.update(
                    output={
                        "published": True,
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

            async with message.process(
                requeue=False
            ):

                payload = json.loads(
                    message.body.decode(
                        "utf-8"
                    )
                )

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
                    )

                    try:

                        await handler(
                            payload
                        )

                    except Exception as exc:

                        if (
                            trace_span
                            is not None
                        ):

                            trace_span.update(
                                level="ERROR",
                                status_message=(
                                    str(exc)
                                ),
                            )

                        raise

                    if trace_span is not None:

                        trace_span.update(
                            output={
                                "processed": (
                                    True
                                )
                            }
                        )

        await queue.consume(
            on_message
        )

        self._logger().info(
            "rabbitmq_consumer_started",
            queue=queue_name,
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

        self._logger().info(
            "rabbitmq_disconnected"
        )