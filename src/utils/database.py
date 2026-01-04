from sqlalchemy import create_engine

from src.model.models import Base
from sqlalchemy.engine import Engine

def create_database_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    **kwargs
) -> Engine:
    """
    Create a SQLAlchemy engine.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        pool_size: Number of connections to maintain
        max_overflow: Max overflow connections
        pool_pre_ping: Test connections before using
        pool_recycle: Recycle connections after N seconds
        **kwargs: Additional arguments
    
    Returns:
        SQLAlchemy engine instance
    """
    engine_args = {
        'echo': echo,
        'pool_pre_ping': pool_pre_ping,
    }
    
    # Only add pool settings for PostgreSQL
    if database_url.startswith('postgresql'):
        engine_args.update({
            'pool_size': pool_size,
            'max_overflow': max_overflow,
            'pool_recycle': pool_recycle,
        })
    
    return create_engine(database_url, **engine_args)


def init_database(engine):
    """
    Initialize the database by creating all tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(engine)
