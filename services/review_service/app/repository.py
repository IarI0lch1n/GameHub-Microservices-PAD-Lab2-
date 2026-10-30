from sqlalchemy import select

from sqlalchemy.orm import Session

from services.review_service.app.models import (
    Review,
)


class ReviewRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def get_review(
        self,
        review_id: int,
    ) -> Review | None:

        return (
            self.session.execute(
                select(
                    Review
                ).where(
                    Review.id
                    == review_id
                )
            )
            .scalar_one_or_none()
        )

    def get_user_game_review(
        self,
        *,
        user_id: int,
        game_id: int,
    ) -> Review | None:

        return (
            self.session.execute(
                select(
                    Review
                ).where(
                    Review.user_id
                    == user_id,
                    Review.game_id
                    == game_id,
                )
            )
            .scalar_one_or_none()
        )

    def list_game_reviews(
        self,
        *,
        game_id: int,
    ) -> list[Review]:

        return list(
            self.session.execute(
                select(
                    Review
                )
                .where(
                    Review.game_id
                    == game_id
                )
                .order_by(
                    Review.created_at.desc()
                )
            )
            .scalars()
            .all()
        )

    def create_review(
        self,
        *,
        user_id: int,
        game_id: int,
        game_title: str,
        rating: int,
        content: str,
    ) -> Review:

        review = Review(
            user_id=user_id,
            game_id=game_id,
            game_title=game_title,
            rating=rating,
            content=content.strip(),
        )

        self.session.add(
            review
        )

        self.session.commit()

        self.session.refresh(
            review
        )

        return review

    def update_review(
        self,
        *,
        review: Review,
        data: dict,
    ) -> Review:

        if (
            "rating" in data
            and data["rating"] is not None
        ):
            review.rating = (
                data["rating"]
            )

        if (
            "content" in data
            and data["content"] is not None
        ):
            review.content = (
                data["content"].strip()
            )

        self.session.commit()

        self.session.refresh(
            review
        )

        return review

    def delete_review(
        self,
        review: Review,
    ) -> None:

        self.session.delete(
            review
        )

        self.session.commit()