import logging

import streamlit as st
from omegaconf import DictConfig

from src.service.finance_service import FinanceService
from src.utils.database import create_database_engine

logger = logging.getLogger(__name__)


@st.cache_resource
def get_database_service(_cfg: DictConfig) -> FinanceService:
    """
    Create and cache the database service.

    Args:
        _cfg: Hydra configuration (underscore prefix prevents hashing)

    Returns:
        FinanceService: Database service instance
    """
    logger.info(f"Connecting to database: {_cfg.db.url}")

    engine = create_database_engine(database_url=_cfg.db.url, echo=_cfg.db.echo)

    service = FinanceService(engine)
    service.create_tables()

    logger.info("✓ Database service initialized")
    return service
