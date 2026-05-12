# git-precommit-pylinters

## What this project does

This tool installs a pre-commit git hook into a target project's `.git/hooks/` directory. The hook runs **ruff** (format + lint) automatically before each commit. It also writes a ruff config block into the target project's `pyproject.toml`.

The installer is run **from this repo** against a **separate target project directory** — it is not a linting tool itself, it's an installer for one.

## Current state (as of May 2026)

The ruff migration is **complete**. The old black/isort/flake8 toolchain has been fully replaced:

- `install.sh` checks/installs `ruff` only
- `install.py` writes a `[tool.ruff]` config block (and subsections) into the target's `pyproject.toml`
- `templates/pre-commit.sh` runs `ruff format` then `ruff check --fix`
- Old templates (`black.pyproject.toml`, `isort.pyproject.toml`, `flake8`) are deleted
- This repo's own `pyproject.toml` is ruff-only (old `[tool.black]` and `[tool.isort]` sections removed)
- This repo's own `.flake8` is deleted

## File structure

```
install.sh                    # Bash entry point: checks requirements, installs ruff, calls install.py
install.py                    # Python installer: ConfigInstaller + HookInstaller (see below)
templates/
  pre-commit.sh               # Git hook template — runs ruff format + ruff check --fix
  ruff.pyproject.toml         # Ruff config template written into target's pyproject.toml
pyproject.toml                # This repo's own ruff config (reference only)
```

## install.py architecture

Two classes, both inherit from `InstallerBase`:

- **`ConfigInstaller`** — strips any existing `[tool.ruff*]` sections from the target's `pyproject.toml`, then appends the ruff template with placeholders filled in. Supports `--line-length` (default 120) and `--target-version` (default py312). Constants `DEFAULT_LINE_LENGTH` and `DEFAULT_TARGET_VERSION` are defined on the class.

- **`HookInstaller`** — writes `templates/pre-commit.sh` (with `{%%USEVENV%%}` / `{%%VENVDIR%%}` substituted) into `<target>/.git/hooks/pre-commit` and makes it executable. Backs up any existing hook to `.bak`.

## install.sh flow

1. OS check (Linux/Mac only)
2. Parse flags: `-h` help, `-s` skip packages, `-w` hook only, `-c` config only, `-l #` line length (optional)
3. Detect active virtualenv (`$VIRTUAL_ENV`)
4. `--config-only`: call `install.py --config-only [--line-length=N]`, exit
5. Validate target `.git` directory exists
6. Check git is installed
7. `--githook-only`: call `install.py --githook-only [--venv $VIRTUAL_ENV]`, exit
8. Check python3 ≥ 3.11 and pip3
9. Check/install ruff (unless `-s`)
10. Call `install.py [--line-length=N] [--venv $VIRTUAL_ENV]`

## Template placeholder system

Both templates use `{%%...%%}` placeholders substituted at install time:

| Template | Placeholder | Source |
|---|---|---|
| `pre-commit.sh` | `{%%USEVENV%%}` | `"0"` if venv given, `"1"` otherwise |
| `pre-commit.sh` | `{%%VENVDIR%%}` | venv path, or `"."` if none |
| `ruff.pyproject.toml` | `{%%LINE_LENGTH%%}` | `--line-length` arg, or `120` |
| `ruff.pyproject.toml` | `{%%TARGET_VERSION%%}` | `--target-version` arg, or `py312` |

## Key design notes

- `ConfigInstaller._strip_ruff_sections()` removes all `[tool.ruff*]` sections before writing — makes re-runs idempotent without TOML parsing.
- `install.sh` uses bash arrays to build `install.py` args, so optional flags (line length, venv) are cleanly included only when set.
- `-l` flag requires an extra `shift` in the while loop to consume its value argument — without it the value bleeds into `DIR`.
