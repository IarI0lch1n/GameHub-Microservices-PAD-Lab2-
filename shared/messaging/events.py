from dataclasses import (
    asdict,
    dataclass,
)

from datetime import (
    datetime,
    timezone,
)

from uuid import uuid4


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    occurred_at: str
    correlation_id: str
    data: dict

    def to_dict(
        self,
    ) -> dict:
        return asdict(
            self
        )


def create_event(
    *,
    event_type: str,
    correlation_id: str,
    data: dict,
) -> EventEnvelope:
    """
    Create the common event envelope used
    by all GameHub microservices.
    """

    return EventEnvelope(
        event_id=str(
            uuid4()
        ),
        event_type=event_type,
        occurred_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        correlation_id=(
            correlation_id
        ),
        data=data,
    )