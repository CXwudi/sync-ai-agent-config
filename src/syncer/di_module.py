"""Dependency injection configuration module."""
from injector import Module, provider, singleton
from .dummy import DummyCalculator


class DIModule(Module):
    """Dependency injection module configuration."""

    @provider
    @singleton
    def provide_dummy_calculator(self) -> DummyCalculator:
        """Provide DummyCalculator instance."""
        return DummyCalculator()
