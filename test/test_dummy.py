"""Tests for dummy.py module."""
import pytest
from injector import Injector
from syncer.dummy import DummyCalculator
from syncer.di_module import DIModule


@pytest.fixture
def calculator():
    """Provide DummyCalculator instance for testing."""
    injector = Injector([DIModule()])
    return injector.get(DummyCalculator)


def test_dummy_add(calculator: DummyCalculator):
    """Test DummyCalculator.add method with positive numbers."""
    assert calculator.add(2, 3) == 5


def test_dummy_add_zero(calculator: DummyCalculator):
    """Test DummyCalculator.add method with zero."""
    assert calculator.add(0, 5) == 5
    assert calculator.add(10, 0) == 10


def test_dummy_add_negative(calculator: DummyCalculator):
    """Test DummyCalculator.add method with negative numbers."""
    assert calculator.add(-1, 1) == 0
    assert calculator.add(-5, -3) == -8


@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (10, 20, 30),
    (-1, -1, -2),
    (100, -50, 50),
])
def test_dummy_add_parametrized(calculator: DummyCalculator, a: int, b: int, expected: int):
    """Test DummyCalculator.add method with various parameter combinations."""
    assert calculator.add(a, b) == expected