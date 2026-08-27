from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from bot.database.connection import SessionLocal
from bot.database.models import Expense, Income, User
from bot.database.users import get_user_by_telegram_id
from bot.utils.authorization import is_authorized


def next_month(month: date) -> date:
    if month.month == 12:
        return month.replace(year=month.year + 1, month=1)
    return month.replace(month=month.month + 1)


def get_monthly_expense_totals(
    telegram_user_id: int,
    current_month: date,
) -> dict[date, tuple[int, Decimal]]:
    """Return count and total for the current and following calendar months."""
    visible_user_ids = get_visible_user_ids(telegram_user_id)
    next_calendar_month = next_month(current_month)
    month_after_next = next_month(next_calendar_month)
    totals = {
        current_month: (0, Decimal("0.00")),
        next_calendar_month: (0, Decimal("0.00")),
    }

    if not visible_user_ids:
        return totals

    with SessionLocal() as session:
        statement = select(Expense.expense_month, Expense.amount).where(
            Expense.user_id.in_(visible_user_ids),
            Expense.expense_month >= current_month,
            Expense.expense_month < month_after_next,
        )

        for expense_month, amount in session.execute(statement):
            month = expense_month.replace(day=1)
            count, total = totals[month]
            totals[month] = (count + 1, total + amount)

    return totals


def get_monthly_income_totals(
    telegram_user_id: int,
    current_month: date,
) -> dict[date, Decimal]:
    visible_user_ids = get_visible_user_ids(telegram_user_id)
    next_calendar_month = next_month(current_month)
    month_after_next = next_month(next_calendar_month)
    totals = {
        current_month: Decimal("0.00"),
        next_calendar_month: Decimal("0.00"),
    }

    if not visible_user_ids:
        return totals

    with SessionLocal() as session:
        statement = select(Income.income_month, Income.amount).where(
            Income.user_id.in_(visible_user_ids),
            Income.income_month >= current_month,
            Income.income_month < month_after_next,
        )

        for income_month, amount in session.execute(statement):
            month = income_month.replace(day=1)
            totals[month] += amount

    return totals


def save_monthly_income(
    telegram_user_id: int,
    amount: Decimal,
    income_month: date,
) -> bool:
    if not is_authorized(telegram_user_id):
        return False

    income_month = income_month.replace(day=1)

    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(User.telegram_id == telegram_user_id)
        )
        if user is None:
            return False

        income = session.scalar(
            select(Income).where(
                Income.user_id == user.id,
                Income.income_month == income_month,
            )
        )

        if income is None:
            session.add(
                Income(
                    user_id=user.id,
                    amount=amount,
                    income_month=income_month,
                )
            )
        else:
            income.amount += amount

        session.commit()
        return True


def get_monthly_financial_summary(
    telegram_user_id: int,
    month: date,
) -> tuple[int, Decimal, Decimal]:
    month = month.replace(day=1)
    expense_count, expenses = get_monthly_expense_totals(
        telegram_user_id,
        month,
    )[month]
    income = get_monthly_income_totals(telegram_user_id, month)[month]
    return expense_count, income, expenses


def delete_monthly_financial_records(month: date):
    """Remove detailed income and expense records for an archived month."""
    month = month.replace(day=1)
    following_month = next_month(month)

    with SessionLocal() as session:
        session.execute(
            delete(Expense).where(
                Expense.expense_month >= month,
                Expense.expense_month < following_month,
            )
        )
        session.execute(
            delete(Income).where(
                Income.income_month >= month,
                Income.income_month < following_month,
            )
        )
        session.commit()


def get_visible_user_ids(
    telegram_user_id: int,
) -> list[int]:
    if not is_authorized(telegram_user_id):
        return []

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
    amount: Decimal,
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
