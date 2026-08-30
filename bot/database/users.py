from sqlalchemy import select

from bot.database.connection import SessionLocal
from bot.database.models import User
from bot.config import OWNER_ID


def get_or_create_user(
    telegram_id: int,
    name: str,
) -> User:
    with SessionLocal() as session:
        statement = select(User).where(
            User.telegram_id == telegram_id
        )

        user = session.scalar(statement)

        if user is not None:
            return user

        user = User(
            telegram_id=telegram_id,
            name=name,
            is_owner=(
                telegram_id == OWNER_ID
            ),
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user


def get_user_by_telegram_id(
    telegram_id: int,
) -> User | None:
    with SessionLocal() as session:
        statement = select(User).where(
            User.telegram_id == telegram_id
        )

        return session.scalar(statement)
