"""
Application dependency injection system.

Provides centralized dependency management following best practices.
"""

from typing import Optional
from functools import lru_cache

from api.core.demo_executor import DemoExecutor
from api.core.config_manager import ConfigManager


class AppDependencies:
    """Application dependencies container."""
    
    def __init__(self):
        self._demo_executor: Optional[DemoExecutor] = None
        self._config_manager: Optional[ConfigManager] = None
    
    @property
    def demo_executor(self) -> DemoExecutor:
        """Get or create demo executor instance."""
        if self._demo_executor is None:
            self._demo_executor = DemoExecutor()
        return self._demo_executor
    
    @property
    def config_manager(self) -> ConfigManager:
        """Get or create config manager instance."""
        if self._config_manager is None:
            self._config_manager = ConfigManager()
        return self._config_manager
    
    def shutdown(self):
        """Clean shutdown of all dependencies."""
        if self._demo_executor:
            self._demo_executor.shutdown()


@lru_cache()
def get_app_dependencies() -> AppDependencies:
    """Get the application dependencies singleton."""
    return AppDependencies()


def get_demo_executor() -> DemoExecutor:
    """FastAPI dependency for demo executor."""
    return get_app_dependencies().demo_executor


def get_config_manager() -> ConfigManager:
    """FastAPI dependency for config manager."""
    return get_app_dependencies().config_manager