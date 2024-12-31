from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import StaticPool


def make_db(database_url: Optional[str] = None) -> Engine:
    """Create a database engine using SQLAlchemy.

    Args:
        database_url: Optional database URL. Defaults to in-memory SQLite.

    Returns:
        SQLAlchemy Engine instance
    """
    if database_url is None:
        database_url = "sqlite:///:memory:"

    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )

    return create_engine(
        database_url,
        # For SQLite in-memory DB, use StaticPool to maintain a single connection
        poolclass=StaticPool if database_url == "sqlite:///:memory:" else None,
        connect_args=connect_args,
        # Echo SQL for debugging
        echo=False,
    )
