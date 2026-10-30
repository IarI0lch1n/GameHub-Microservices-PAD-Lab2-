from sqlalchemy import select

from sqlalchemy.orm import Session

from services.library_service.app.models import (
    LibraryItem,
)


class LibraryRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def get_by_order_id(
        self,
        order_id: int,
    ) -> LibraryItem | None:

        return (
            self.session.execute(
                select(
                    LibraryItem
                ).where(
                    LibraryItem.order_id
                    == order_id
                )
            )
            .scalar_one_or_none()
        )

    def get_user_game(
        self,
        *,
        user_id: int,
        game_id: int,
    ) -> LibraryItem | None:

        return (
            self.session.execute(
                select(
                    LibraryItem
                ).where(
                    LibraryItem.user_id
                    == user_id,
                    LibraryItem.game_id
                    == game_id,
                )
            )
            .scalar_one_or_none()
        )

    def list_user_library(
        self,
        *,
        user_id: int,
    ) -> list[LibraryItem]:

        return list(
            self.session.execute(
                select(
                    LibraryItem
                )
                .where(
                    LibraryItem.user_id
                    == user_id
                )
                .order_by(
                    LibraryItem
                    .acquired_at
                    .desc()
                )
            )
            .scalars()
            .all()
        )

    def create_item(
        self,
        *,
        user_id: int,
        game_id: int,
        order_id: int,
        game_title: str,
        purchase_price,
    ) -> LibraryItem:

        item = LibraryItem(
            user_id=user_id,
            game_id=game_id,
            order_id=order_id,
            game_title=game_title,
            purchase_price=(
                purchase_price
            ),
        )

        self.session.add(
            item
        )

        self.session.commit()

        self.session.refresh(
            item
        )

        return item