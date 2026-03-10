# Run tests
test:
  uv run pytest tests

# Type check
typecheck:
  uv run ty check src/sync_ai_config tests

# Lint
lint:
  uv run ruff check .

# Format
format:
  uv run ruff format .

# Build executable
build-exe:
  uv run pyinstaller src/sync_ai_config/cli.py --name sync-ai-config --onefile
