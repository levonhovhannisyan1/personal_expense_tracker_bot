from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select

from bot.database.connection import SessionLocal
from bot.database.models import Expense, Income, MonthlySummary, SavingsSetting, User
from bot.services.expense_service import (
    get_monthly_expense_totals,
    get_monthly_income_totals,
    get_visible_user_ids,
    next_month,
)
from bot.utils.authorization import is_authorized


def set_opening_savings(
    telegram_user_id: int,
    opening_balance: Decimal,
    effective_month: date,
) -> bool:
    if not is_authorized(telegram_user_id):
        return False

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.telegram_id == telegram_user_id))
        if user is None:
            return False

        setting = session.scalar(
            select(SavingsSetting).where(SavingsSetting.user_id == user.id)
        )
        if setting is None:
            session.add(
                SavingsSetting(
                    user_id=user.id,
                    opening_balance=opening_balance,
                    effective_month=effective_month.replace(day=1),
                )
            )
        else:
            setting.opening_balance = opening_balance
            setting.effective_month = effective_month.replace(day=1)
        session.commit()
        return True


def get_monthly_closing_balances(
    telegram_user_id: int,
    current_month: date,
) -> dict[date, Decimal]:
    current_month = current_month.replace(day=1)
    following_month = next_month(current_month)
    visible_user_ids = get_visible_user_ids(telegram_user_id)
    balances = {current_month: Decimal("0.00"), following_month: Decimal("0.00")}

    if not visible_user_ids:
        return balances

    with SessionLocal() as session:
        opening_balance = Decimal("0.00")
        for user_id in visible_user_ids:
            previous_summary = session.scalar(
                select(MonthlySummary.closing_balance)
                .where(
                    MonthlySummary.user_id == user_id,
                    MonthlySummary.summary_month < current_month,
                )
                .order_by(MonthlySummary.summary_month.desc())
            )
            if previous_summary is not None:
                opening_balance += previous_summary
                continue

            setting = session.scalar(
                select(SavingsSetting).where(SavingsSetting.user_id == user_id)
            )
            if setting and setting.effective_month <= current_month:
                opening_balance += setting.opening_balance

    expenses = get_monthly_expense_totals(telegram_user_id, current_month)
    incomes = get_monthly_income_totals(telegram_user_id, current_month)
    balances[current_month] = (
        opening_balance + incomes[current_month] - expenses[current_month][1]
    )
    balances[following_month] = (
        balances[current_month]
        + incomes[following_month]
        - expenses[following_month][1]
    )
    return balances


def archive_monthly_financial_records(month: date):
    """Persist compact monthly snapshots, then remove archived detail rows."""
    month = month.replace(day=1)
    following_month = next_month(month)

    with SessionLocal() as session:
        already_archived = session.scalar(
            select(MonthlySummary.id).where(MonthlySummary.summary_month == month)
        )
        if already_archived is not None:
            return

        users = session.scalars(select(User)).all()
        for user in users:
            income = sum(
                session.scalars(
                    select(Income.amount).where(
                        Income.user_id == user.id,
                        Income.income_month >= month,
                        Income.income_month < following_month,
                    )
                ),
                Decimal("0.00"),
            )
            expenses = sum(
                session.scalars(
                    select(Expense.amount).where(
                        Expense.user_id == user.id,
                        Expense.expense_month >= month,
                        Expense.expense_month < following_month,
                    )
                ),
                Decimal("0.00"),
            )
            previous_balance = session.scalar(
                select(MonthlySummary.closing_balance)
                .where(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.summary_month < month,
                )
                .order_by(MonthlySummary.summary_month.desc())
            )
            setting = session.scalar(
                select(SavingsSetting).where(SavingsSetting.user_id == user.id)
            )
            opening_balance = previous_balance or Decimal("0.00")
            if previous_balance is None and setting and setting.effective_month <= month:
                opening_balance = setting.opening_balance

            if income or expenses or previous_balance is not None or opening_balance:
                savings = income - expenses
                session.add(
                    MonthlySummary(
                        user_id=user.id,
                        summary_month=month,
                        income=income,
                        expenses=expenses,
                        savings=savings,
                        closing_balance=opening_balance + savings,
                    )
                )

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
