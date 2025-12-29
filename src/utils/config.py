import logging
from pathlib import Path
from hydra import initialize_config_dir, compose
from omegaconf import DictConfig
import streamlit as st

logger = logging.getLogger(__name__)


@st.cache_resource
def load_hydra_config() -> DictConfig:
    """
    Load Hydra configuration (cached to avoid reloading).

    Returns:
        DictConfig: Hydra configuration object
    """
    config_dir = Path(__file__).parent.parent / "conf"
    print(f"Loading Hydra config from: {config_dir}")
    config_dir = config_dir.resolve()

    with initialize_config_dir(config_dir=str(config_dir), version_base=None):
        cfg = compose(config_name="config")

    logger.info("✓ Hydra configuration loaded")
    return cfg


@st.cache_resource
def setup_logging(_cfg: DictConfig) -> None:
    """
    Setup logging configuration.

    Args:
        cfg: Hydra configuration
    """
    logging.basicConfig(level=getattr(logging, _cfg.logging.level), format=_cfg.logging.format)
    logger.info("✓ Logging configured")
