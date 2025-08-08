# Python Code Style Guide

Essential Python coding standards for the sync-ai-agent-config project.

## Basic Standards

- **Type Hints**: Use for all function parameters, return types, and complex variables
- **Docstrings**: Google style for all functions and classes  
- **Logging**: Use `logging` module with % formatting, logger at file level: `logger = logging.getLogger(__name__)`

```python
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process data with logging."""
    
    def process_items(self, items: List[str]) -> int:
        """Process a list of items."""
        logger.info("Processing %s items", len(items))
        return len(items)
```

## Object-Oriented Programming

- **Class Design**: Use classes for core logic, keep focused and cohesive
- **Composition over Inheritance**: Prefer composition for flexibility
- **Constructor Injection**: Plain constructors without DI decorators

```python
class EmailService:
    """Service for sending emails."""
    
    def __init__(self, smtp_client: SMTPClient):
        self._smtp_client = smtp_client
        
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email using the SMTP client."""
        return self._smtp_client.send(to, subject, body)
```

## Dependency Injection

### Core Rule: No DI Imports in Business Logic

**CRITICAL**: Business logic classes must never import `injector`. All DI configuration happens exclusively in `di_module.py`.

### Business Logic Classes

Keep clean of DI imports - use plain constructor injection:

```python
# ✅ Good: Clean business logic
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, email_service: EmailService, config_manager: ConfigurationManager):
        self._email_service = email_service
        self._config_manager = config_manager
```

### DI Module Structure

All DI configuration in `di_module.py`:

```python
# di_module.py - ONLY place with DI imports
from injector import Module, provider, singleton

class DIModule(Module):
    """Dependency injection module configuration."""
    
    @provider
    @singleton
    def provide_configuration_manager(self) -> ConfigurationManager:
        """Provide ConfigurationManager instance."""
        return ConfigurationManager("config.yaml")
```

## Testing Standards

- **pytest**: Use descriptive test names
- **Manual DI**: No DI framework in tests, use mocks
- **Coverage**: Maintain 90%+ coverage with pytest-cov

```python
import pytest
from unittest.mock import Mock

class TestNotificationService:
    """Test cases for NotificationService."""
    
    def test_send_notification_calls_email_service_correctly(self):
        """Test notification service calls email service correctly."""
        mock_email_service = Mock()
        mock_config_manager = Mock()
        
        service = NotificationService(mock_email_service, mock_config_manager)
        # Test implementation
```

## Code Organization

### Module Structure

```
src/syncer/
├── main.py           # Entry point (only place with DI imports)
├── di_module.py      # All dependency injection configuration  
├── services/         # Business logic (no DI imports)
├── clients/          # External integrations (no DI imports)
└── models/           # Data models (no DI imports)
```

### Import Order

```python
# Standard library
import logging
from typing import Dict, List

# Third-party (excluding DI framework)
import requests

# Local application
from syncer.models import ConfigModel
```

### Naming Conventions

- **Classes**: PascalCase (`ConfigurationManager`)
- **Functions/Variables**: snake_case (`send_email`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`)
- **Private**: Leading underscore (`self._config`)

## Error Handling

Use specific exception types with meaningful messages:

```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

def sync_configs(self, source: str, dest: str) -> bool:
    """Sync configurations."""
    try:
        if not os.path.exists(source):
            raise ConfigurationError(f"Source path does not exist: {source}")
        return True
    except OSError as e:
        logger.error("File system error: %s", e)
        raise ConfigurationError(f"Sync failed: {e}") from e
```

## Performance & Best Practices

- **Lazy Loading**: Use `@cached_property` for expensive operations
- **Context Managers**: For resource management
- **Minimal Comments**: Only for complex business logic
- **Documentation**: Keep README and API docs updated

This style guide ensures clean, maintainable code with proper separation of concerns.