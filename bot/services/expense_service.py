from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from bot.database.connection import SessionLocal
from bot.database.models import Expense, User
from bot.database.users import get_user_by_telegram_id


def get_visible_user_ids(
    telegram_user_id: int,
) -> list[int]:
    user = get_user_by_telegram_id(
        telegram_user_id
    )

    if user is None:
        return []

    if not user.is_owner:
        return [user.id]

    with SessionLocal() as session:
        statement = select(User)

        users = session.scalars(
            statement
        ).all()

        return [
            user.id
            for user in users
        ]


def get_user_expenses(
    telegram_user_id: int,
    limit: int = 10,
) -> list[Expense]:
    visible_user_ids = get_visible_user_ids(
        telegram_user_id
    )

    if not visible_user_ids:
        return []

    with SessionLocal() as session:
        statement = (
            select(Expense)
            .options(
                joinedload(Expense.user)
            )
            .where(
                Expense.user_id.in_(
                    visible_user_ids
                )
            )
            .order_by(
                Expense.expense_month.desc(),
                Expense.created_at.desc(),
            )
            .limit(limit)
        )

        return session.scalars(
            statement
        ).unique().all()


def get_expense(
    telegram_user_id: int,
    expense_id: int,
) -> Expense | None:
    visible_user_ids = get_visible_user_ids(
        telegram_user_id
    )

    if not visible_user_ids:
        return None

    with SessionLocal() as session:
        statement = (
            select(Expense)
            .options(
                joinedload(Expense.user)
            )
            .where(
                Expense.id == expense_id,
                Expense.user_id.in_(
                    visible_user_ids
                ),
            )
        )

        return session.scalar(statement)


def update_expense(
    telegram_user_id: int,
    expense_id: int,
    category: str,
    amount: float,
    description: str,
    expense_month: date,
) -> bool:
    visible_user_ids = get_visible_user_ids(
        telegram_user_id
    )

    if not visible_user_ids:
        return False

    with SessionLocal() as session:
        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id.in_(visible_user_ids),
            )
        )

        expense = session.scalar(statement)

        if expense is None:
            return False

        expense.category = category
        expense.amount = amount
        expense.description = description
        expense.expense_month = expense_month

        session.commit()

        return True


def delete_expense(
    telegram_user_id: int,
    expense_id: int,
) -> bool:
    visible_user_ids = get_visible_user_ids(
        telegram_user_id
    )

    if not visible_user_ids:
        return False

    with SessionLocal() as session:
        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id.in_(
                    visible_user_ids
                ),
            )
        )

        expense = session.scalar(statement)

        if expense is None:
            return False

        session.delete(expense)
        session.commit()

        return True