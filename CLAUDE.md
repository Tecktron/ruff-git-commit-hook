# ruff-git-commit-hook (Ruff Git Commit-hook Installer)

> This file is a [CLAUDE.md](https://docs.anthropic.com/en/docs/claude-code/memory) — project context loaded automatically by Claude Code (Anthropic's AI coding assistant). It is safe to ignore if you are not using Claude Code.

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
2. Parse flags: `-h` help, `-s` skip packages, `-w` hook only, `-c` config only, `-l #` line length, `-t v` target version, `-d` no Django rules, `-p path` toml path, `-b path` lint dir
3. Detect active virtualenv (`$VIRTUAL_ENV`) or auto-detect one in the target dir (`.venv`, `venv`, `env`)
4. `--config-only`: check python3 ≥ 3.11, call `install.py --config-only [--line-length=N] [--target-version=V] [--no-django] [--toml-path=P]`, exit
5. Validate target `.git` directory exists
6. Check git is installed
7. If venv active/detected: check/install ruff inside venv, set `RUFF_PATH`
8. If no venv: check python3 ≥ 3.11, check pip3 (update pip), check/install ruff globally, set `RUFF_PATH`
9. `--githook-only`: call `install.py --githook-only --ruff-path=RUFF_PATH [--venv $VIRTUAL_ENV] [--lint-dir=D]`, exit
10. Call `install.py [--line-length=N] [--target-version=V] [--no-django] [--toml-path=P] --ruff-path=RUFF_PATH [--venv $VIRTUAL_ENV] [--lint-dir=D]`

## Template placeholder system

Both templates use `{%%...%%}` placeholders substituted at install time:

| Template | Placeholder | Source |
|---|---|---|
| `pre-commit.sh` | `{%%USEVENV%%}` | `"0"` if venv given, `"1"` otherwise |
| `pre-commit.sh` | `{%%VENVDIR%%}` | venv path, or `"."` if none |
| `pre-commit.sh` | `{%%RUFFBIN%%}` | absolute path to ruff binary |
| `pre-commit.sh` | `{%%LINTDIR%%}` | relative path to lint directory, or `"."` for project root |
| `ruff.pyproject.toml` | `{%%LINE_LENGTH%%}` | `--line-length` arg, or `120` |
| `ruff.pyproject.toml` | `{%%TARGET_VERSION%%}` | `--target-version` arg, or `py312` |
| `ruff.pyproject.toml` | `{%%DJANGO%%}` | `"DJ", ` normally, `""` when `--no-django` is passed |

## Code quality

All Python code written for this project must pass the ruff linter and formatter. Run `ruff check .` and `ruff format --check .` before considering any change complete.

## Key design notes

- `ConfigInstaller._strip_ruff_sections()` removes all `[tool.ruff*]` sections before writing — makes re-runs idempotent without TOML parsing.
- `install.sh` uses bash arrays to build `install.py` args, so optional flags (line length, venv) are cleanly included only when set.
- `-l` flag requires an extra `shift` in the while loop to consume its value argument — without it the value bleeds into `DIR`.
