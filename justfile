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
  uv run pyinstaller src/sync_ai_config/main.py --name sync-ai-config --onefile --add-data src/sync_ai_config/default_mappings.toml:sync_ai_config
