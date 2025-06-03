# Make ignis config directory a Python package
from importlib import reload

# Export settings for easy import
from .options import settings

__all__ = ["settings", "reload"]