#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path


class InstallerBase:
    TEMPLATE_DIR = Path(__file__).parent / "templates"
    TEMPLATES = {}

    @staticmethod
    def get_full_path(path_name: str) -> str:
        return str(Path(os.path.expandvars(path_name)).expanduser().resolve())

    @classmethod
    def get_and_check_path(cls, path_name: str) -> str:
        path_name = cls.get_full_path(path_name)
        if not Path(path_name).is_dir():
            raise AssertionError(f'Error: "{path_name}" is not a directory')
        return path_name

    @staticmethod
    def write_to_file(filename, data):
        Path(filename).write_text(data, encoding="utf-8")

    @classmethod
    def load_template_file(cls, template):
        filename = cls.TEMPLATES.get(template, {}).get("file", "")
        if not filename:
            raise AssertionError(f"Error: No file configured for {template}")
        filepath = cls.TEMPLATE_DIR / filename
        if not filepath.is_file():
            raise AssertionError(f'Error: Template file "{filepath}" not found')
        return filepath.read_text()


class ConfigInstaller(InstallerBase):
    TEMPLATES = {"RUFF": {"file": "ruff.pyproject.toml"}}

    DEFAULT_LINE_LENGTH = 120
    DEFAULT_TARGET_VERSION = "py312"
    DEFAULT_NO_DJANGO = False

    def __init__(self, target_dir, line_length=None, target_version=None, no_django=False):
        self.target_dir = self.get_and_check_path(target_dir)
        self.line_length = int(line_length) if line_length else None
        self.target_version = str(target_version) if target_version else None
        self.no_django = bool(no_django)
        self.toml_file = Path(self.target_dir) / "pyproject.toml"

    def _strip_ruff_sections(self, toml_data: str) -> str:
        """Remove all existing [tool.ruff*] sections so they can be replaced cleanly."""
        lines = toml_data.split("\n")
        result = []
        in_ruff = False
        for line in lines:
            if line.strip().startswith("["):
                in_ruff = line.strip().startswith("[tool.ruff]") or line.strip().startswith("[tool.ruff.")
            if not in_ruff:
                result.append(line)
        return ("\n".join(result).rstrip("\n")).strip() + "\n"

    def _apply_overrides(self, template: str) -> str:
        line_length = self.line_length if self.line_length else self.DEFAULT_LINE_LENGTH
        target_version = self.target_version if self.target_version else self.DEFAULT_TARGET_VERSION
        django_entry = "" if self.no_django else '"DJ", '
        template = template.replace("{%%LINE_LENGTH%%}", str(line_length))
        template = template.replace("{%%TARGET_VERSION%%}", target_version)
        template = template.replace("{%%DJANGO%%}", django_entry)
        return template

    def install(self):
        existing = ""
        if self.toml_file.is_file():
            existing = self.toml_file.read_text()

        base = self._strip_ruff_sections(existing)
        template = self._apply_overrides(self.load_template_file("RUFF"))

        if base.strip():
            base = base.rstrip("\n") + "\n\n"
        else:
            base = ""

        self.write_to_file(self.toml_file, base + template)


class HookInstaller(InstallerBase):
    TEMPLATES = {"PRE_COMMIT": {"file": "pre-commit.sh"}}

    def __init__(self, target_dir, venv_dir=None, ruff_path=None):
        git_path = Path(target_dir) / ".git"
        if git_path.is_dir():
            hooks_path = str(git_path / "hooks")
        elif git_path.is_file():
            gitdir_text = git_path.read_text().strip()
            if not gitdir_text.startswith("gitdir: "):
                raise AssertionError(f'Error: Cannot parse .git file at "{git_path}"')
            gitdir = Path(gitdir_text[8:])
            if not gitdir.is_absolute():
                gitdir = Path(target_dir) / gitdir
            # worktree gitdir is <common>/.git/worktrees/<name>; hooks live two levels up
            hooks_path = str(gitdir.parent.parent / "hooks")
        else:
            raise AssertionError(f'Error: No .git directory or file found at "{target_dir}"')
        self.git_hook_dir = Path(self.get_and_check_path(hooks_path))
        self.venv_dir = self.get_full_path(venv_dir) if venv_dir else None
        self.ruff_path = ruff_path or "ruff"

    def generate_template(self):
        template = self.load_template_file("PRE_COMMIT")
        template = template.replace("{%%USEVENV%%}", "0" if self.venv_dir else "1")
        template = template.replace("{%%VENVDIR%%}", self.venv_dir if self.venv_dir else ".")
        template = template.replace("{%%RUFFBIN%%}", self.ruff_path)
        return template

    def install(self):
        hook_file = self.git_hook_dir / "pre-commit"
        if hook_file.is_file():
            shutil.copy2(hook_file, hook_file.parent / (hook_file.name + ".bak"))
        hook_data = self.generate_template()
        self.write_to_file(hook_file, hook_data)
        hook_file.chmod(hook_file.stat().st_mode | 0o111)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Precommit Ruff Setup",
        description=(
            "Sets up and configures a pre-commit git hook that automatically runs ruff "
            "(format + lint) on your code before each commit."
        ),
    )

    parser.add_argument(
        "--line-length",
        required=False,
        default=None,
        type=int,
        dest="line_length",
        metavar="120",
        help=f"Line length for ruff (optional, defaults to {ConfigInstaller.DEFAULT_LINE_LENGTH})",
    )

    parser.add_argument(
        "--target-version",
        required=False,
        default=None,
        type=str,
        dest="target_version",
        metavar="py312",
        help=f"Target Python version for ruff (optional, defaults to {ConfigInstaller.DEFAULT_TARGET_VERSION})",
    )

    parser.add_argument(
        "--ruff-path",
        required=False,
        default="ruff",
        type=str,
        dest="ruff_path",
        metavar="/path/to/ruff",
        help="Absolute path to the ruff binary to embed in the hook (defaults to 'ruff')",
    )

    parser.add_argument(
        "--venv",
        required=False,
        default=None,
        type=str,
        dest="venv_dir",
        metavar="/path/to/venv",
        help="Activate this virtual environment before running ruff in the hook",
    )

    parser.add_argument(
        "--no-django",
        required=False,
        default=False,
        action="store_true",
        dest="no_django",
        help="Exclude Django-specific lint rules (DJ) from the ruff config",
    )

    parser.add_argument(
        "--config-only",
        required=False,
        default=False,
        action="store_true",
        dest="config_only",
        help="Only write config files; skip installing the git hook",
    )

    parser.add_argument(
        "--githook-only",
        required=False,
        default=False,
        action="store_true",
        dest="githook_only",
        help="Only install the git hook; skip writing config files",
    )

    parser.add_argument("install_directory", type=str, help="Target project directory")

    argsd = vars(parser.parse_args())
    target_dir = argsd["install_directory"]

    if not argsd["githook_only"]:
        ConfigInstaller(target_dir, argsd["line_length"], argsd["target_version"], argsd["no_django"]).install()

    if not argsd["config_only"]:
        HookInstaller(target_dir, argsd["venv_dir"], argsd["ruff_path"]).install()
