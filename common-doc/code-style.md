# Python Code Style Guide

This document provides comprehensive Python coding standards for the sync-ai-agent-config project.

## Basic Standards

### Type Hints

Always use type hints for function parameters, return types, and non-obvious variables.

```python
def add_numbers(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b

# For complex types
from typing import List, Dict, Optional

def process_data(items: List[str], config: Dict[str, str]) -> Optional[str]:
    """Process a list of items with configuration."""
    if not items:
        return None
    return config.get("output", "default")
```

### Docstrings

All functions and classes must have docstrings following Google style:

```python
class Calculator:
    """Calculator for basic arithmetic operations.
    
    This class provides methods for performing basic mathematical
    operations with proper logging and error handling.
    """
    
    def divide(self, dividend: float, divisor: float) -> float:
        """Divide two numbers.
        
        Args:
            dividend: The number to be divided.
            divisor: The number to divide by.
            
        Returns:
            The result of the division.
            
        Raises:
            ValueError: If divisor is zero.
        """
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return dividend / divisor
```

### Logging

Use the `logging` module with % formatting. Place logger at the class level for each file:

```python
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process data with logging."""
    
    def process_items(self, items: List[str]) -> int:
        """Process a list of items."""
        logger.info("Processing %s items", len(items))
        
        for i, item in enumerate(items):
            logger.debug("Processing item %s: %s", i, item)
            
        logger.info("Completed processing %s items", len(items))
        return len(items)
```

## Object-Oriented Programming

### Class Design

Use classes for core logic components. Keep classes focused and cohesive:

```python
class ConfigurationManager:
    """Manages application configuration settings."""
    
    def __init__(self, config_path: str):
        self._config_path = config_path
        self._config: Dict[str, str] = {}
        
    def load_config(self) -> None:
        """Load configuration from file."""
        logger.info("Loading configuration from %s", self._config_path)
        # Implementation here
        
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a configuration setting."""
        return self._config.get(key, default)
```

### Composition Over Inheritance

Prefer composition over inheritance for flexibility:

```python
# Good: Composition
class EmailService:
    """Service for sending emails."""
    
    def __init__(self, smtp_client: SMTPClient):
        self._smtp_client = smtp_client
        
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email using the SMTP client."""
        return self._smtp_client.send(to, subject, body)

# Instead of: Inheritance
class EmailService(SMTPClient):  # Avoid this pattern
    pass
```

## Dependency Injection

### Core Principle: No DI Imports in Business Logic

**IMPORTANT**: Business logic classes should never import or use dependency injection decorators. All DI configuration happens exclusively in `di_module.py`.

### Business Logic Classes

Keep business logic classes clean of DI imports - use plain constructor injection:

```python
# ✅ Good: Clean business logic without DI imports
import logging
from typing import List

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, email_service: EmailService, config_manager: ConfigurationManager):
        self._email_service = email_service
        self._config_manager = config_manager
        
    def send_notification(self, user_email: str, message: str) -> bool:
        """Send notification to user."""
        subject = self._config_manager.get_setting("notification_subject", "Notification")
        logger.info("Sending notification to %s", user_email)
        return self._email_service.send_email(user_email, subject, message)

class SyncService:
    """Service for synchronizing configurations."""
    
    def __init__(self, rsync_client: RsyncClient, config_manager: ConfigurationManager):
        self._rsync_client = rsync_client
        self._config_manager = config_manager
        
    def sync_configs(self, source_path: str, dest_path: str) -> bool:
        """Sync configurations from source to destination."""
        timeout = self._config_manager.get_setting("sync_timeout", "30")
        logger.info("Syncing from %s to %s with timeout %s", source_path, dest_path, timeout)
        return self._rsync_client.sync(source_path, dest_path, int(timeout))
```

### Dependency Injection Module

All DI configuration happens in `di_module.py` using the `injector` library:

```python
# di_module.py - All DI imports and configuration here
from injector import Module, provider, singleton
from syncer.services.notification_service import NotificationService
from syncer.services.sync_service import SyncService
from syncer.services.email_service import EmailService
from syncer.services.config_manager import ConfigurationManager
from syncer.clients.smtp_client import SMTPClient
from syncer.clients.rsync_client import RsyncClient

class DIModule(Module):
    """Dependency injection module configuration."""
    
    @provider
    @singleton
    def provide_configuration_manager(self) -> ConfigurationManager:
        """Provide ConfigurationManager instance."""
        return ConfigurationManager("config.yaml")
    
    @provider
    @singleton  
    def provide_smtp_client(self) -> SMTPClient:
        """Provide SMTP client instance."""
        return SMTPClient("smtp.example.com", 587)
    
    @provider
    @singleton
    def provide_rsync_client(self) -> RsyncClient:
        """Provide Rsync client instance."""
        return RsyncClient()
        
    @provider
    @singleton
    def provide_email_service(self, smtp_client: SMTPClient) -> EmailService:
        """Provide EmailService with injected SMTP client."""
        return EmailService(smtp_client)
        
    @provider
    @singleton
    def provide_notification_service(
        self, 
        email_service: EmailService, 
        config_manager: ConfigurationManager
    ) -> NotificationService:
        """Provide NotificationService with injected dependencies."""
        return NotificationService(email_service, config_manager)
        
    @provider
    @singleton
    def provide_sync_service(
        self, 
        rsync_client: RsyncClient, 
        config_manager: ConfigurationManager
    ) -> SyncService:
        """Provide SyncService with injected dependencies."""
        return SyncService(rsync_client, config_manager)
```

### Application Entry Point

Use the injector only at the application entry point:

```python
# main.py - DI container setup at entry point only
from injector import Injector
from syncer.di_module import DIModule
from syncer.services.sync_service import SyncService

def main() -> None:
    """Application entry point."""
    injector = Injector([DIModule()])
    sync_service = injector.get(SyncService)
    
    # Use the service
    success = sync_service.sync_configs("/source", "/dest")
    if success:
        print("Sync completed successfully")
    else:
        print("Sync failed")

if __name__ == "__main__":
    main()
```

## Testing Standards

### Test Structure

Use pytest for testing with descriptive test names:

```python
import pytest
from syncer.dummy import DummyCalculator

class TestDummyCalculator:
    """Test cases for DummyCalculator."""
    
    def test_add_positive_numbers_returns_correct_sum(self):
        """Test that adding positive numbers returns correct sum."""
        calculator = DummyCalculator()
        
        result = calculator.add(2, 3)
        
        assert result == 5
        
    def test_add_negative_numbers_returns_correct_sum(self):
        """Test that adding negative numbers works correctly."""
        calculator = DummyCalculator()
        
        result = calculator.add(-2, -3)
        
        assert result == -5
        
    @pytest.mark.parametrize("a,b,expected", [
        (0, 0, 0),
        (1, -1, 0),
        (100, 200, 300),
    ])
    def test_add_various_combinations(self, a: int, b: int, expected: int):
        """Test addition with various number combinations."""
        calculator = DummyCalculator()
        
        result = calculator.add(a, b)
        
        assert result == expected
```

### Testing with Dependencies

Test business logic classes with manual dependency injection (no DI framework in tests):

```python
import pytest
from unittest.mock import Mock
from syncer.services.notification_service import NotificationService

class TestNotificationService:
    """Test cases for NotificationService."""
    
    def test_send_notification_calls_email_service_with_correct_parameters(self):
        """Test that notification service calls email service correctly."""
        # Arrange
        mock_email_service = Mock()
        mock_config_manager = Mock()
        mock_config_manager.get_setting.return_value = "Test Subject"
        mock_email_service.send_email.return_value = True
        
        service = NotificationService(mock_email_service, mock_config_manager)
        
        # Act
        result = service.send_notification("user@example.com", "Test message")
        
        # Assert
        assert result is True
        mock_config_manager.get_setting.assert_called_once_with("notification_subject", "Notification")
        mock_email_service.send_email.assert_called_once_with("user@example.com", "Test Subject", "Test message")
```

### Test Coverage

Maintain high test coverage using pytest-cov. Configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=syncer",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=90"
]
```

## Code Organization

### Module Structure

Organize code into logical modules:

```
src/
├── syncer/
│   ├── __init__.py
│   ├── main.py           # Entry point (only place with DI imports)
│   ├── di_module.py      # All dependency injection configuration
│   ├── services/         # Business logic (no DI imports)
│   │   ├── __init__.py
│   │   ├── sync_service.py
│   │   └── config_service.py
│   ├── clients/          # External integrations (no DI imports)
│   │   ├── __init__.py
│   │   └── rsync_client.py
│   └── models/           # Data models (no DI imports)
│       ├── __init__.py
│       └── config_model.py
```

### Import Organization

Organize imports in this order, avoiding DI imports in business logic:

```python
# Standard library imports
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports (excluding DI framework)
import requests
import yaml

# Local application imports
from syncer.models import ConfigModel
from syncer.clients import RsyncClient
```

### Naming Conventions

- **Classes**: PascalCase (`ConfigurationManager`, `EmailService`)
- **Functions/Variables**: snake_case (`send_email`, `config_path`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private attributes**: Leading underscore (`self._config`, `self._client`)

## Error Handling

### Exception Handling

Use specific exception types and provide meaningful error messages:

```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

class SyncService:
    """Service for synchronizing configurations."""
    
    def sync_configs(self, source_path: str, dest_path: str) -> bool:
        """Sync configurations from source to destination."""
        try:
            if not os.path.exists(source_path):
                raise ConfigurationError(f"Source path does not exist: {source_path}")
                
            # Sync logic here
            logger.info("Successfully synced from %s to %s", source_path, dest_path)
            return True
            
        except OSError as e:
            logger.error("File system error during sync: %s", e)
            raise ConfigurationError(f"Sync failed due to file system error: {e}") from e
        except Exception as e:
            logger.error("Unexpected error during sync: %s", e)
            raise
```

## Performance Considerations

### Lazy Loading

Use lazy loading for expensive operations:

```python
from functools import cached_property

class ConfigurationManager:
    """Configuration manager with lazy loading."""
    
    @cached_property
    def parsed_config(self) -> Dict[str, str]:
        """Parse configuration file (cached after first access)."""
        logger.info("Parsing configuration file")
        # Expensive parsing operation
        return self._parse_config_file()
```

### Resource Management

Use context managers for resource handling:

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def database_connection() -> Generator[Connection, None, None]:
    """Context manager for database connections."""
    conn = create_connection()
    try:
        logger.debug("Database connection established")
        yield conn
    finally:
        conn.close()
        logger.debug("Database connection closed")

# Usage
def save_data(data: Dict[str, str]) -> None:
    """Save data to database."""
    with database_connection() as conn:
        conn.execute("INSERT INTO data VALUES (?)", data)
```

## Documentation Standards

### Code Comments

Use comments sparingly for complex business logic:

```python
def calculate_sync_priority(self, config: ConfigModel) -> int:
    """Calculate synchronization priority based on configuration."""
    base_priority = config.priority
    
    # Boost priority for configurations that haven't been synced recently
    # Priority increases logarithmically with days since last sync
    days_since_sync = (datetime.now() - config.last_sync).days
    time_boost = int(math.log(max(1, days_since_sync)))
    
    return base_priority + time_boost
```

### README and Documentation

Keep documentation up-to-date and include:
- Installation instructions
- Usage examples
- API documentation
- Contributing guidelines

This style guide should be followed consistently across all Python code in the project. Regular code reviews should ensure adherence to these standards.