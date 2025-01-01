default:
    @just --list

test:
    @uv run pytest

test-s:
    @uv run pytest -s

ruff:
    uv run ruff format lab

pyright:
    uv run pyright lab

lint:
    just ruff
    just pyright

lint-file file:
    - ruff {{file}}
    - pyright {{file}}

