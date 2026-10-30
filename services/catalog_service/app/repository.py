import re
import unicodedata

from uuid import (
    uuid4,
)

from sqlalchemy import (
    func,
    or_,
    select,
)

from sqlalchemy.orm import (
    Session,
    selectinload,
)

from services.catalog_service.app.models import (
    Game,
    Genre,
)


def _slugify(
    value: str,
) -> str:
    normalized = (
        unicodedata
        .normalize(
            "NFKD",
            value,
        )
        .encode(
            "ascii",
            "ignore",
        )
        .decode(
            "ascii"
        )
        .lower()
    )

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    ).strip(
        "-"
    )

    if slug:
        return slug

    return (
        "item-"
        + uuid4().hex[:8]
    )


class CatalogRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    #
    # Genres
    #

    def list_genres(
        self,
    ) -> list[Genre]:
        return list(
            self.session.execute(
                select(
                    Genre
                ).order_by(
                    Genre.name.asc()
                )
            )
            .scalars()
            .all()
        )

    def get_genre_by_name(
        self,
        name: str,
    ) -> Genre | None:
        return (
            self.session.execute(
                select(
                    Genre
                ).where(
                    func.lower(
                        Genre.name
                    )
                    == name.strip().lower()
                )
            )
            .scalar_one_or_none()
        )

    def get_genres_by_ids(
        self,
        genre_ids: list[int],
    ) -> list[Genre]:
        if not genre_ids:
            return []

        unique_ids = list(
            dict.fromkeys(
                genre_ids
            )
        )

        return list(
            self.session.execute(
                select(
                    Genre
                ).where(
                    Genre.id.in_(
                        unique_ids
                    )
                )
            )
            .scalars()
            .all()
        )

    def _unique_genre_slug(
        self,
        name: str,
    ) -> str:
        base_slug = _slugify(
            name
        )

        candidate = base_slug
        counter = 2

        while (
            self.session.execute(
                select(
                    Genre.id
                ).where(
                    Genre.slug
                    == candidate
                )
            )
            .scalar_one_or_none()
            is not None
        ):
            candidate = (
                f"{base_slug}-{counter}"
            )

            counter += 1

        return candidate

    def create_genre(
        self,
        *,
        name: str,
    ) -> Genre:
        genre = Genre(
            name=name.strip(),
            slug=(
                self._unique_genre_slug(
                    name
                )
            ),
        )

        self.session.add(
            genre
        )

        self.session.commit()

        self.session.refresh(
            genre
        )

        return genre

    #
    # Games
    #

    def get_game(
        self,
        game_id: int,
    ) -> Game | None:
        return (
            self.session.execute(
                select(
                    Game
                )
                .options(
                    selectinload(
                        Game.genres
                    )
                )
                .where(
                    Game.id
                    == game_id
                )
            )
            .scalar_one_or_none()
        )

    def _unique_game_slug(
        self,
        title: str,
        *,
        exclude_game_id: (
            int
            | None
        ) = None,
    ) -> str:
        base_slug = _slugify(
            title
        )

        candidate = base_slug
        counter = 2

        while True:
            statement = (
                select(
                    Game.id
                )
                .where(
                    Game.slug
                    == candidate
                )
            )

            if (
                exclude_game_id
                is not None
            ):
                statement = (
                    statement.where(
                        Game.id
                        != exclude_game_id
                    )
                )

            existing = (
                self.session.execute(
                    statement
                )
                .scalar_one_or_none()
            )

            if existing is None:
                return candidate

            candidate = (
                f"{base_slug}-{counter}"
            )

            counter += 1

    def list_games(
        self,
        *,
        search: (
            str
            | None
        ) = None,
        genre: (
            str
            | None
        ) = None,
        min_price: (
            float
            | None
        ) = None,
        max_price: (
            float
            | None
        ) = None,
        published: (
            bool
            | None
        ) = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Game]:
        statement = (
            select(
                Game
            )
            .options(
                selectinload(
                    Game.genres
                )
            )
        )

        if search:
            pattern = (
                "%"
                + search.strip()
                + "%"
            )

            statement = (
                statement.where(
                    or_(
                        Game.title.ilike(
                            pattern
                        ),
                        Game.developer.ilike(
                            pattern
                        ),
                        Game.publisher.ilike(
                            pattern
                        ),
                    )
                )
            )

        if genre:
            normalized_genre = (
                genre
                .strip()
                .lower()
            )

            statement = (
                statement
                .join(
                    Game.genres
                )
                .where(
                    or_(
                        func.lower(
                            Genre.name
                        )
                        == normalized_genre,

                        Genre.slug
                        == normalized_genre,
                    )
                )
                .distinct()
            )

        if (
            min_price
            is not None
        ):
            statement = (
                statement.where(
                    Game.price
                    >= min_price
                )
            )

        if (
            max_price
            is not None
        ):
            statement = (
                statement.where(
                    Game.price
                    <= max_price
                )
            )

        if (
            published
            is not None
        ):
            statement = (
                statement.where(
                    Game.is_published
                    == published
                )
            )

        statement = (
            statement
            .order_by(
                Game.title.asc()
            )
            .offset(
                skip
            )
            .limit(
                limit
            )
        )

        return list(
            self.session.execute(
                statement
            )
            .scalars()
            .unique()
            .all()
        )

    def create_game(
        self,
        *,
        title: str,
        description: (
            str
            | None
        ),
        price: float,
        release_date,
        developer: (
            str
            | None
        ),
        publisher: (
            str
            | None
        ),
        is_published: bool,
        genres: list[Genre],
    ) -> Game:
        game = Game(
            title=title.strip(),
            slug=(
                self._unique_game_slug(
                    title
                )
            ),
            description=description,
            price=price,
            release_date=(
                release_date
            ),
            developer=developer,
            publisher=publisher,
            is_published=(
                is_published
            ),
            genres=genres,
        )

        self.session.add(
            game
        )

        self.session.commit()

        return self.get_game(
            game.id
        )

    def update_game(
        self,
        *,
        game: Game,
        data: dict,
        genres: (
            list[Genre]
            | None
        ) = None,
    ) -> Game:
        if (
            "title" in data
            and data["title"]
            is not None
        ):
            game.title = (
                data["title"]
                .strip()
            )

            game.slug = (
                self._unique_game_slug(
                    game.title,
                    exclude_game_id=(
                        game.id
                    ),
                )
            )

        for field in (
            "description",
            "price",
            "release_date",
            "developer",
            "publisher",
            "is_published",
        ):
            if field in data:
                setattr(
                    game,
                    field,
                    data[field],
                )

        if genres is not None:
            game.genres = genres

        self.session.commit()

        return self.get_game(
            game.id
        )

    def delete_game(
        self,
        game: Game,
    ) -> None:
        self.session.delete(
            game
        )

        self.session.commit()