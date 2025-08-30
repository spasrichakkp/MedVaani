"""Timeout handler utilities for async operations."""

import asyncio
from typing import Any, Awaitable, Optional

from ..logging.logger_factory import get_module_logger


class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass


class TimeoutHandler:
    """Run async operations with timeouts in a consistent way."""

    def __init__(self, default_timeout: Optional[float] = None):
        self.default_timeout = default_timeout
        self.logger = get_module_logger(__name__)

    async def run(self, coro: Awaitable[Any], timeout: Optional[float] = None) -> Any:
        """Run a coroutine with a timeout."""
        try:
            return await asyncio.wait_for(coro, timeout or self.default_timeout)
        except asyncio.TimeoutError as e:
            self.logger.error(f"Operation timed out after {timeout or self.default_timeout}s")
            raise TimeoutError(str(e)) from e


async def run_with_timeout(coro: Awaitable[Any], timeout: float) -> Any:
    """Convenience function to run a coroutine with a timeout."""
    handler = TimeoutHandler()
    return await handler.run(coro, timeout)
