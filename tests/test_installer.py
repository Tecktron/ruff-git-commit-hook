import stat
from pathlib import Path

import pytest

from install import ConfigInstaller, HookInstaller

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_hooks_dir(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# ConfigInstaller._strip_ruff_sections
# ---------------------------------------------------------------------------


class TestStripRuffSections:
    @pytest.fixture
    def installer(self, tmp_path):
        return ConfigInstaller(str(tmp_path))

    def test_empty_string(self, installer):
        assert installer._strip_ruff_sections("") == "\n"

    def test_no_ruff_sections_preserved(self, installer):
        content = "[tool.black]\nline-length = 88\n"
        result = installer._strip_ruff_sections(content)
        assert "[tool.black]" in result
        assert "[tool.ruff" not in result

    def test_strips_ruff_section(self, installer):
        content = "[tool.black]\nline-length = 88\n\n[tool.ruff]\nline-length = 120\n"
        result = installer._strip_ruff_sections(content)
        assert "[tool.black]" in result
        assert "[tool.ruff]" not in result

    def test_strips_all_ruff_subsections(self, installer):
        content = (
            "[tool.ruff]\nline-length = 120\n\n"
            "[tool.ruff.lint]\nselect = []\n\n"
            '[tool.ruff.format]\nquote-style = "double"\n'
        )
        result = installer._strip_ruff_sections(content)
        assert "[tool.ruff]" not in result
        assert "[tool.ruff.lint]" not in result
        assert "[tool.ruff.format]" not in result

    def test_preserves_sections_after_ruff(self, installer):
        content = "[tool.ruff]\nline-length = 120\n\n[build-system]\nrequires = []\n"
        result = installer._strip_ruff_sections(content)
        assert "[tool.ruff]" not in result
        assert "[build-system]" in result

    def test_result_ends_with_newline(self, installer):
        assert installer._strip_ruff_sections("").endswith("\n")
        assert installer._strip_ruff_sections("[tool.ruff]\nfoo = 1\n").endswith("\n")

    def test_does_not_strip_ruff_lsp_section(self, installer):
        content = "[tool.ruff-lsp]\nsettings = {}\n\n[tool.ruff]\nline-length = 120\n"
        result = installer._strip_ruff_sections(content)
        assert "[tool.ruff-lsp]" in result
        assert "[tool.ruff]" not in result


# ---------------------------------------------------------------------------
# ConfigInstaller._apply_overrides
# ---------------------------------------------------------------------------


SIMPLE_TEMPLATE = (
    'line-length = {%%LINE_LENGTH%%}\ntarget-version = "{%%TARGET_VERSION%%}"\nselect = ["E", {%%DJANGO%%}"F"]\n'
)


class TestApplyOverrides:
    def test_default_line_length(self, tmp_path):
        result = ConfigInstaller(str(tmp_path))._apply_overrides(SIMPLE_TEMPLATE)
        assert "line-length = 120" in result

    def test_custom_line_length(self, tmp_path):
        result = ConfigInstaller(str(tmp_path), line_length=88)._apply_overrides(SIMPLE_TEMPLATE)
        assert "line-length = 88" in result

    def test_default_target_version(self, tmp_path):
        result = ConfigInstaller(str(tmp_path))._apply_overrides(SIMPLE_TEMPLATE)
        assert 'target-version = "py312"' in result

    def test_custom_target_version(self, tmp_path):
        result = ConfigInstaller(str(tmp_path), target_version="py311")._apply_overrides(SIMPLE_TEMPLATE)
        assert 'target-version = "py311"' in result

    def test_django_included_by_default(self, tmp_path):
        result = ConfigInstaller(str(tmp_path))._apply_overrides(SIMPLE_TEMPLATE)
        assert '"DJ"' in result

    def test_django_excluded_when_no_django(self, tmp_path):
        result = ConfigInstaller(str(tmp_path), no_django=True)._apply_overrides(SIMPLE_TEMPLATE)
        assert '"DJ"' not in result

    def test_no_unresolved_placeholders(self, tmp_path):
        result = ConfigInstaller(str(tmp_path))._apply_overrides(SIMPLE_TEMPLATE)
        assert "{%%" not in result


# ---------------------------------------------------------------------------
# ConfigInstaller.install
# ---------------------------------------------------------------------------


class TestConfigInstallerInstall:
    def test_creates_pyproject_toml_when_missing(self, tmp_path):
        ConfigInstaller(str(tmp_path)).install()
        assert (tmp_path / "pyproject.toml").is_file()

    def test_written_file_contains_ruff_config(self, tmp_path):
        ConfigInstaller(str(tmp_path)).install()
        content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert "[tool.ruff]" in content

    def test_appends_to_existing_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[build-system]\nrequires = []\n", encoding="utf-8")
        ConfigInstaller(str(tmp_path)).install()
        content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert "[build-system]" in content
        assert "[tool.ruff]" in content

    def test_replaces_existing_ruff_config(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.ruff]\nline-length = 79\n\n[tool.ruff.lint]\nselect = ["E"]\n',
            encoding="utf-8",
        )
        ConfigInstaller(str(tmp_path), line_length=120).install()
        content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert "line-length = 120" in content
        assert "line-length = 79" not in content

    def test_idempotent(self, tmp_path):
        ConfigInstaller(str(tmp_path)).install()
        first = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        ConfigInstaller(str(tmp_path)).install()
        second = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert first == second

    def test_no_django_excludes_dj_rules(self, tmp_path):
        ConfigInstaller(str(tmp_path), no_django=True).install()
        content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert '"DJ"' not in content

    def test_django_included_by_default(self, tmp_path):
        ConfigInstaller(str(tmp_path)).install()
        content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert '"DJ"' in content


# ---------------------------------------------------------------------------
# HookInstaller.generate_template
# ---------------------------------------------------------------------------


class TestHookInstallerGenerateTemplate:
    def test_no_venv_sets_use_venv_1(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        result = HookInstaller(str(target)).generate_template()
        assert "USE_VENV=1" in result

    def test_with_venv_sets_use_venv_0(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        venv = tmp_path / "venv"
        venv.mkdir()
        result = HookInstaller(str(target), venv_dir=str(venv)).generate_template()
        assert "USE_VENV=0" in result

    def test_ruff_path_substituted(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        result = HookInstaller(str(target), ruff_path="/usr/local/bin/ruff").generate_template()
        assert 'RUFF="/usr/local/bin/ruff"' in result

    def test_default_ruff_path(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        result = HookInstaller(str(target)).generate_template()
        assert 'RUFF="ruff"' in result

    def test_no_unresolved_placeholders(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        result = HookInstaller(str(target)).generate_template()
        assert "{%%" not in result

    def test_git_add_exit_code_propagated(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        result = HookInstaller(str(target)).generate_template()
        assert "GIT_ADD_RTN" in result
        assert 'exit "${GIT_ADD_RTN}"' in result


# ---------------------------------------------------------------------------
# HookInstaller.install
# ---------------------------------------------------------------------------


class TestHookInstallerInstall:
    def test_creates_hook_file(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        HookInstaller(str(target)).install()
        assert (target / ".git" / "hooks" / "pre-commit").is_file()

    def test_hook_is_executable(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        HookInstaller(str(target)).install()
        mode = (target / ".git" / "hooks" / "pre-commit").stat().st_mode
        assert mode & stat.S_IXUSR

    def test_backs_up_existing_hook(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        hook = target / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho existing\n", encoding="utf-8")
        HookInstaller(str(target)).install()
        backup = target / ".git" / "hooks" / "pre-commit.bak"
        assert backup.is_file()
        assert "existing" in backup.read_text(encoding="utf-8")

    def test_overwrites_existing_hook(self, tmp_path):
        target = make_hooks_dir(tmp_path)
        hook = target / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho old\n", encoding="utf-8")
        HookInstaller(str(target)).install()
        assert "echo old" not in hook.read_text(encoding="utf-8")

    def test_worktree_resolves_to_common_hooks_dir(self, tmp_path):
        # Simulate a git worktree: main repo has .git/ dir, worktree has .git file
        main_repo = tmp_path / "main"
        main_repo.mkdir()
        (main_repo / ".git" / "hooks").mkdir(parents=True)
        (main_repo / ".git" / "worktrees" / "feature").mkdir(parents=True)

        worktree = tmp_path / "feature"
        worktree.mkdir()
        gitdir_path = main_repo / ".git" / "worktrees" / "feature"
        (worktree / ".git").write_text(f"gitdir: {gitdir_path}\n", encoding="utf-8")

        HookInstaller(str(worktree)).install()
        assert (main_repo / ".git" / "hooks" / "pre-commit").is_file()

    def test_no_git_dir_raises(self, tmp_path):
        with pytest.raises(AssertionError, match="No .git directory or file found"):
            HookInstaller(str(tmp_path))

    def test_malformed_git_file_raises(self, tmp_path):
        (tmp_path / ".git").write_text("not a gitdir pointer\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="Cannot parse .git file"):
            HookInstaller(str(tmp_path))
