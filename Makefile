.PHONY: lint typecheck test clean

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

test:
	uv run pytest

test-cov:
	uv run pytest --cov --cov-report=html --cov-report=term

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
