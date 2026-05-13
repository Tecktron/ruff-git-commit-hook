# Ruff Git Commit-hook Installer

## What it does

Installs a pre-commit git hook that automatically formats and lints Python code using **ruff** before each commit. It also writes a `[tool.ruff]` config block into the target project's `pyproject.toml`.

When the hook runs on commit it:
1. Runs `ruff format` to auto-format code
2. Runs `ruff check --fix` to auto-fix lint issues
3. Re-stages any files modified by the above
4. Aborts the commit if unfixable lint errors remain

## Requirements

1. git
2. Python 3.11+
3. pip
4. A bash-compatible shell

ruff will be installed automatically if not already present — into the active virtual environment if one is active, or globally via pip otherwise. Pass `-s` to skip automatic installation.

## How to install

Run `install.sh` with the path to the project you want to install the hook into:

```bash
bash install.sh /path/to/your/project
```

The installer will:
1. Check/install ruff
2. Write a `[tool.ruff]` config block into the target's `pyproject.toml`
3. Install a pre-commit hook into `<target>/.git/hooks/pre-commit`

If a virtual environment is active (`$VIRTUAL_ENV` is set), or if one is found inside the target directory (`.venv`, `venv`, or `env`), it will be used automatically — ruff will be installed into it if missing, and the hook will activate it before running.

### Install options

| Flag | Description |
|------|-------------|
| `-h` | Show help and exit |
| `-s` | Skip package installation — abort instead of installing ruff if not found |
| `-w` | Git hook only — skip writing `pyproject.toml` config |
| `-c` | Config only — skip installing the git hook |
| `-l #` | Set ruff line length (default: 120) |
| `-t v` | Set Python target version (default: py312) |

Only one of `-w` / `-c` may be used at a time.

### Examples

```bash
# Full install into ~/projects/myapp
bash install.sh ~/projects/myapp

# Install with a custom line length
bash install.sh -l 88 ~/projects/myapp

# Write config only, no hook
bash install.sh -c ~/projects/myapp

# Install hook only, no config changes
bash install.sh -w ~/projects/myapp
```

## Configuration

The installer writes a `[tool.ruff]` block (and subsections) into the target's `pyproject.toml`, replacing any existing ruff config. The block is sourced from `templates/ruff.pyproject.toml`.

Default settings:

| Setting | Default |
|---------|---------|
| `line-length` | 120 |
| `target-version` | py312 |

Override at install time with `-l` (line length) and `-t` (target version). The config can be freely edited after installation.

## Manual installation

To install without the shell script, run `install.py` directly:

```bash
python3 install.py [--line-length 120] [--target-version py312] [--venv /path/to/venv] /path/to/project
python3 install.py --config-only /path/to/project
python3 install.py --githook-only [--venv /path/to/venv] /path/to/project
```

## Help and support

If you find a bug or want to request a feature, please search the [GitHub issues](https://github.com/Tecktron/ruff-git-commit-hook/issues) first. If it doesn't exist, open a new ticket with as much detail as possible about how to reproduce the issue or what you'd like to see.

## Contributing

This is an open source project — contributions are welcome.
