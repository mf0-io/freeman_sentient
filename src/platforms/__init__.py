"""Platform abstraction layer for multi-platform support

Provides extensible framework for integrating with various platforms
including Telegram, Discord, Twitter, and other social platforms.
"""

from .base import BasePlatformAdapter
from .factory import PlatformFactory

__all__ = ['BasePlatformAdapter', 'PlatformFactory']
