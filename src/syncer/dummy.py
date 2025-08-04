"""Dummy calculator module for testing purposes."""
import logging

logger = logging.getLogger(__name__)


class DummyCalculator:
    """Dummy calculator implementation for testing."""
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        logger.info("Adding %s and %s", a, b)
        result = a + b
        logger.info("Result: %s", result)
        return result
