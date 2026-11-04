import pytest

from shared.messaging.rabbitmq import (
    DELIVERY_ATTEMPT_HEADER,
    _get_delivery_attempt,
)


@pytest.mark.parametrize(
    (
        "headers",
        "expected",
    ),
    [
        (
            None,
            1,
        ),
        (
            {},
            1,
        ),
        (
            {
                DELIVERY_ATTEMPT_HEADER:
                    2
            },
            2,
        ),
        (
            {
                DELIVERY_ATTEMPT_HEADER:
                    "3"
            },
            3,
        ),
        (
            {
                DELIVERY_ATTEMPT_HEADER:
                    "invalid"
            },
            1,
        ),
        (
            {
                DELIVERY_ATTEMPT_HEADER:
                    -10
            },
            1,
        ),
    ],
)
def test_delivery_attempt_parsing(
    headers,
    expected: int,
) -> None:

    assert (
        _get_delivery_attempt(
            headers
        )
        == expected
    )