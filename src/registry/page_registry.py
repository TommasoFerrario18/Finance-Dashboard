import logging
from typing import Any

from omegaconf import DictConfig, OmegaConf

from src.mappings.mappings import MAP_PAGES

logger = logging.getLogger(__name__)


class PageRegistry:
    """Registry for dashboard pages loaded from Hydra configuration."""

    def __init__(self, cfg: DictConfig):
        """
        Initialize page registry from Hydra config.

        Args:
            cfg: Hydra configuration containing pages config
        """
        self.cfg = cfg
        self._pages = {}
        self._page_classes = {}
        self._load_pages()

    def _load_pages(self):
        """Load pages from configuration."""
        if not hasattr(self.cfg, "pages"):
            logger.warning("No pages configuration found")
            return

        # Convert to native Python dict for easier use
        pages_list = OmegaConf.to_container(self.cfg.pages, resolve=True)

        # Sort by order
        pages_list = sorted(pages_list, key=lambda x: x.get("order", 999))

        # Build pages dictionary
        for page_config in pages_list:
            if not page_config.get("enabled", True):
                continue

            name = page_config["name"]
            self._pages[name] = {
                "icon": page_config.get("icon", "📄"),
                "class": page_config.get("class"),
                "description": page_config.get("description", ""),
                "order": page_config.get("order", 999),
            }

            # Load the actual class
            self._load_page_class(name, page_config["class"])

        logger.info(f"Loaded {len(self._pages)} pages from configuration")

    def _load_page_class(self, page_name: str, class_name: str):
        """
        Dynamically load page class.

        Args:
            page_name: Name of the page
            class_name: Name of the class to load
        """
        try:
            self._page_classes[page_name] = MAP_PAGES[page_name]
            logger.debug(f"Loaded class {class_name} for page {page_name}")
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load class {class_name}: {e}")
            self._page_classes[page_name] = None

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """
        Convert to dictionary format compatible with legacy code.

        Returns:
            Dictionary with page configs including class objects
        """
        result = {}
        for name, config in self._pages.items():
            result[name] = {
                "icon": config["icon"],
                "class": self._page_classes.get(name),
                "description": config["description"],
            }
        return result


def load_pages_from_config(cfg: DictConfig) -> dict[str, dict[str, Any]]:
    """
    Load pages configuration from Hydra config.

    This is a convenience function that returns a dictionary compatible
    with the original PAGES constant.

    Args:
        cfg: Hydra configuration

    Returns:
        Dictionary of page configurations
    """
    registry = PageRegistry(cfg)
    return registry.to_dict()


def create_page_registry(cfg: DictConfig) -> PageRegistry:
    """
    Create a page registry from Hydra config.

    Args:
        cfg: Hydra configuration

    Returns:
        PageRegistry instance
    """
    return PageRegistry(cfg)
