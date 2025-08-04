# CLAUDE.md

## Documentation-First Approach:

**CRITICAL: Before starting ANY task, you MUST first check the ./common-doc/ directory for relevant guidance and documentation. This is mandatory for all tasks - no exceptions.**

### Before Starting:

1. Use the LS tool to explore ./common-doc/ directory structure
2. Read any relevant documentation files that might relate to your task
3. Use Grep/Glob tools to search for specific guidance if needed
   - Quick tip: Search for lines starting with `#` to find markdown headers and quickly identify relevant sections
4. Only proceed with the task after consulting the documentation

### After Completing:

1. Review if any changes made require updating common documentation in ./common-doc/

## Python Code Style

This section is a simplified version of the [`common-doc/code-style.md`] file.

### Basic

- Use type hints for parameters, return types, and non-intuitive variables
- Use docstrings for functions and classes
- Use `logging` module with % formatting: `logger.info("Processing %s items", count)`
  - put logger on the class level for each file

### OOP and DI

- Use classes for core logic part
- prefer composition over inheritance
- Use dependency injection, `injector`
- all injection goes to `di_module.py` file, with a class implementing the `Module` interface
  - no DI related imports are allowed in business logic files
- the `Module` interface only contains methods decorated with `@provider`
