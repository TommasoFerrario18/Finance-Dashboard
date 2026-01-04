import os
from pathlib import Path

from dotenv import load_dotenv as dotenv_load


def load_env_file(env_path: str | None = None) -> None:
    """
    Load environment variables from .env file.

    This is a simple implementation that doesn't require python-dotenv.

    Args:
        env_path: Path to .env file. If None, searches for .env in current dir and parent dirs.
    """
    if env_path:
        env_file = Path(env_path)
    else:
        # Search for .env in current directory and parent directories
        current = Path.cwd()
        env_file = None

        for directory in [current] + list(current.parents):
            potential_env = directory / ".env"
            if potential_env.exists():
                env_file = potential_env
                break

    if not env_file or not env_file.exists():
        # No .env file found - this is okay, env vars might be set another way
        return

    # Read and parse .env file
    with open(env_file) as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"') or value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable (don't override existing)
                if key not in os.environ:
                    os.environ[key] = value


def load_dotenv() -> None:
    """
    Load environment variables from .env file using python-dotenv if available.
    Falls back to simple implementation if not.
    """
    try:
        dotenv_load()
    except ImportError:
        # Fall back to our simple implementation
        load_env_file()
