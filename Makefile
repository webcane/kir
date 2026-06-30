.PHONY: help test lint fmt run

help:
	@echo "KIR — Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo "  help       Show this help message"
	@echo "  test       Run tests with pytest"
	@echo "  lint       Check code with ruff"
	@echo "  fmt        Format code with ruff"
	@echo "  fmt-check  Check formatting without modifying files"
	@echo "  run        Run pytest (placeholder for app execution)"
	@echo ""

test:
	uv run pytest

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

fmt-check:
	uv run ruff format --check src tests

run: test
	@echo "Application execution placeholder — add your app entry point here"
