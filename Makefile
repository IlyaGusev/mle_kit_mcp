.PHONY: black style validate test install serve

install:
	uv pip install -e .

black:
	uv run black mle_kit_mcp --line-length 100

validate:
	uv run black mle_kit_mcp --line-length 100
	uv run flake8 mle_kit_mcp
	uv run mypy mle_kit_mcp --strict --explicit-package-bases

test:
	uv run pytest -s

publish:
	uv build && uv publish
