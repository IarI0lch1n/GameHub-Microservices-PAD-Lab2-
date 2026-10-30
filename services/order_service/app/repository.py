from sqlalchemy import select

from sqlalchemy.orm import Session

from services.order_service.app.models import (
    Order,
)


class OrderRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def get_existing_purchase(
        self,
        *,
        user_id: int,
        game_id: int,
    ) -> Order | None:

        return (
            self.session.execute(
                select(
                    Order
                ).where(
                    Order.user_id
                    == user_id,
                    Order.game_id
                    == game_id,
                )
            )
            .scalar_one_or_none()
        )

    def get_user_order(
        self,
        *,
        order_id: int,
        user_id: int,
    ) -> Order | None:

        return (
            self.session.execute(
                select(
                    Order
                ).where(
                    Order.id
                    == order_id,
                    Order.user_id
                    == user_id,
                )
            )
            .scalar_one_or_none()
        )

    def list_user_orders(
        self,
        *,
        user_id: int,
    ) -> list[Order]:

        return list(
            self.session.execute(
                select(
                    Order
                )
                .where(
                    Order.user_id
                    == user_id
                )
                .order_by(
                    Order.created_at.desc()
                )
            )
            .scalars()
            .all()
        )

    def create_order(
        self,
        *,
        user_id: int,
        game_id: int,
        game_title: str,
        total_price,
    ) -> Order:

        order = Order(
            user_id=user_id,
            game_id=game_id,
            game_title=game_title,
            total_price=total_price,
            status="completed",
        )

        self.session.add(
            order
        )

        self.session.commit()

        self.session.refresh(
            order
        )

        return order