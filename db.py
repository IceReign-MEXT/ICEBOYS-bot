import os
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from decimal import Decimal
import datetime

# Load DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test_subscriptions.db")

# Base model
Base = declarative_base()

# Subscription table
class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id = Column(String, primary_key=True)
    expires = Column(DateTime)
    plan = Column(String)

# Create engine with fallback to SQLite
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    )
    engine.connect()
except OperationalError as e:
    print(f"[DB] Connection failed: {e}. Falling back to SQLite.")
    DATABASE_URL = "sqlite:///./test_subscriptions.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": True})

# Create tables
Base.metadata.create_all(engine)

# Session factory
Session = sessionmaker(bind=engine)

# --- Helper functions ---
def grant_subscription(user_id: str, days: int = 30):
    session = Session()
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(days=days)
    sub = session.query(Subscription).filter_by(user_id=str(user_id)).first()
    if sub:
        sub.expires = expire
    else:
        sub = Subscription(user_id=str(user_id), expires=expire, plan="automated_monthly")
        session.add(sub)
    session.commit()
    session.close()

def check_subscription(user_id: str) -> bool:
    session = Session()
    sub = session.query(Subscription).filter_by(user_id=str(user_id)).first()
    session.close()
    return sub and sub.expires > datetime.datetime.now(datetime.timezone.utc)