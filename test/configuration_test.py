from dataclasses import FrozenInstanceError
from pathlib import Path
import sys

import pytest

from configuration import ConfigurationError, TexactConfig, load_config
from texact import set_up_arg_parser


def test_no_configuration_returns_defaults(tmp_path: Path) -> None:
    config = load_config(directory=tmp_path)

    assert config == TexactConfig()
    assert config.source_path is None


def test_discovery_precedence(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.texact.lint]\nwe_count = 2\n", encoding="utf-8"
    )
    (tmp_path / "texact.toml").write_text("[lint]\nwe_count = 3\n", encoding="utf-8")
    (tmp_path / ".texact.toml").write_text("[lint]\nwe_count = 4\n", encoding="utf-8")

    config = load_config(directory=tmp_path)

    assert config.lint.we_count == 4
    assert config.source_path == tmp_path / ".texact.toml"


def test_pyproject_configuration_is_used(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.texact.lint]\nignore = ['FIG002']\n", encoding="utf-8"
    )

    config = load_config(directory=tmp_path)

    assert config.lint.ignore == frozenset({"FIG002"})


def test_supported_settings_are_parsed(tmp_path: Path) -> None:
    (tmp_path / ".texact.toml").write_text(
        "[lint]\n"
        "casing = ['LaTeX']\n"
        "we_count = 7\n"
        "\n"
        "[format]\n"
        "html-style = true\n"
        "\n"
        "[tools]\n"
        "chktex_path = '/usr/bin'\n",
        encoding="utf-8",
    )

    config = load_config(directory=tmp_path)

    assert config.lint.casing == ("LaTeX",)
    assert config.lint.we_count == 7
    assert config.format.html_style is True
    assert config.tools.chktex_path == "/usr/bin"


def test_explicit_configuration_has_highest_precedence(tmp_path: Path) -> None:
    (tmp_path / ".texact.toml").write_text("[lint]\nwe_count = 4\n", encoding="utf-8")
    explicit_path = tmp_path / "explicit.toml"
    explicit_path.write_text("[lint]\nwe_count = 9\n", encoding="utf-8")

    config = load_config(config_path=explicit_path, directory=tmp_path)

    assert config.lint.we_count == 9
    assert config.source_path == explicit_path


def test_invalid_toml_has_a_clear_error(tmp_path: Path) -> None:
    config_path = tmp_path / ".texact.toml"
    config_path.write_text("[lint\nwe_count = 4\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid TOML"):
        load_config(directory=tmp_path)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("[lint]\nwe_count = 'seven'\n", "lint.we_count"),
        ("[lint]\nunknown = true\n", "unsupported option 'lint.unknown'"),
        ("[format]\nhtml-style = 'yes'\n", "format.html-style"),
        ("[tools]\nchktex_path = 4\n", "tools.chktex_path"),
    ],
)
def test_invalid_values_have_clear_errors(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    (tmp_path / ".texact.toml").write_text(content, encoding="utf-8")

    with pytest.raises(ConfigurationError, match=message):
        load_config(directory=tmp_path)


def test_configuration_dataclasses_are_frozen() -> None:
    config = TexactConfig()

    with pytest.raises(FrozenInstanceError):
        config.lint = config.lint


def test_explicit_cli_values_are_distinguishable_from_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "texact",
            "--config",
            "custom.toml",
            "--no-html-style",
            "--no-unsure",
            "file.tex",
        ],
    )

    args = set_up_arg_parser()

    assert args.config == Path("custom.toml")
    assert args.html_style is False
    assert args.unsure is False
    assert args.chktex is None
