import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.database.models import Base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///family_finance.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(engine)
