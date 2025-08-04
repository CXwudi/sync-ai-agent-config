# CLAUDE.md

## Python Code Style

- Use type hints for parameters, return types, and non-intuitive variables
- Use docstrings for functions and classes
- Use `logging` module with % formatting: `logger.info("Processing %s items", count)`
  - put logger on the class level for each file

## OOP and DI

- Use classes for core logic part
- prefer composition over inheritance
- Use dependency injection, `injector`
- all injection goes to `di_module.py` file, with a class implementing the `Module` interface
- the `Module` interface only contains methods decorated with `@provider`