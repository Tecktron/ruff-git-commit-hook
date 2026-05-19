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
| `-d` | Exclude Django lint rules (`DJ`) from the ruff config |
| `-p path` | Directory containing the `pyproject.toml` to write the ruff config into. Accepts an absolute path or a path relative to the install directory. Defaults to the install directory. Ignored (with a warning) when used with `-w`. |
| `-b path` | Restrict the hook to only lint staged files under this directory. Accepts an absolute path or a path relative to the install directory. Defaults to the project root. Ignored when used with `-c`. |

If both `-w` and `-c` are passed, `-c` takes precedence — only the config is written and the hook is not installed.

### Examples

```bash
# Full install into ~/projects/myapp
bash install.sh ~/projects/myapp

# Install with a custom line length
bash install.sh -l 88 ~/projects/myapp

# Install without Django lint rules
bash install.sh -d ~/projects/myapp

# Write config only, no hook
bash install.sh -c ~/projects/myapp

# Install hook only, no config changes
bash install.sh -w ~/projects/myapp

# Write ruff config into a subdirectory's pyproject.toml
bash install.sh -p ./backend ~/projects/myapp

# Write ruff config into a pyproject.toml at an absolute path
bash install.sh -p /srv/configs ~/projects/myapp

# Only lint staged files under the backend/ subdirectory
bash install.sh -b ./backend ~/projects/myapp

# Combined: custom toml location and restricted lint directory
bash install.sh -p ./backend -b ./backend ~/projects/myapp
```

## Configuration

The installer writes a `[tool.ruff]` block (and subsections) into the target's `pyproject.toml`, replacing any existing ruff config. The block is sourced from `templates/ruff.pyproject.toml`.

Default settings:

| Setting | Default |
|---------|---------|
| `line-length` | 120 |
| `target-version` | py312 |
| Django rules (`DJ`) | enabled |

Override at install time with `-l` (line length), `-t` (target version), and `-d` (disable Django rules). The config can be freely edited after installation.

## Manual installation

To install without the shell script, run `install.py` directly:

```bash
python3 install.py [--line-length 120] [--target-version py312] [--no-django] [--toml-path /path/to/dir] [--ruff-path /path/to/ruff] [--venv /path/to/venv] [--lint-dir path/to/dir] /path/to/project
python3 install.py --config-only [--line-length 120] [--target-version py312] [--no-django] [--toml-path /path/to/dir] /path/to/project
python3 install.py --githook-only [--ruff-path /path/to/ruff] [--venv /path/to/venv] [--lint-dir path/to/dir] /path/to/project
```
## Help and support

If you find a bug or want to request a feature, please search the [GitHub issues](https://github.com/Tecktron/ruff-git-commit-hook/issues) first. If it doesn't exist, open a new ticket with as much detail as possible about how to reproduce the issue or what you'd like to see.

## Contributing

This is an open source project — contributions are welcome.
