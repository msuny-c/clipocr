# Simple Makefile for ClipGPT-OCR

# Use poetry to find the python interpreter in the virtual environment
PYTHON = $(shell poetry run which python)
PIP = $(shell poetry run which pip)
CLIPOCR = $(shell poetry run which clipocr)

.PHONY: help install run lint clean build-exe

help:
	@echo "Available commands:"
	@echo "  install        Install dependencies using Poetry (use --with dev for test/lint tools)"
	@echo "  run            Run the script once (requires image in clipboard). Pass args via ARGS='-p prompt_name'."
	@echo "  lint           Lint code using ruff"
	@echo "  clean          Remove build artifacts and cache files"
	@echo "  build-exe      Build a standalone executable using PyInstaller (requires PyInstaller)"

install: pyproject.toml poetry.lock
	@echo ">>> Installing dependencies..."
	@poetry install --no-root

# Usage: make run ARGS="-p markdown"
run:
	@echo ">>> Running ClipGPT-OCR..."
	@$(CLIPOCR) $(ARGS) # Pass arguments via ARGS variable

lint:
	@echo ">>> Linting with ruff..."
	@poetry run ruff check .

clean:
	@echo ">>> Cleaning up..."
	@rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov *.spec __pycache__ clipgpt_ocr/__pycache__ .venv
	@find . -name '*.pyc' -delete
	@find . -name '*.pyo' -delete

# Requires pyinstaller (install with `poetry install --with dev`) and Python < 3.13
build-exe:
	@echo ">>> Building executable with PyInstaller..."
	@echo "    (Ensure dev dependencies are installed: 'poetry install --with dev')"
	@poetry run pyinstaller --onefile --name clipocr --add-data "prompts:prompts" cli.py

# Default empty ARGS for make run
ARGS ?= ""

# Allow overriding ARGS from command line, e.g., make run ARGS="-p markdown"