import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

_CONFIG_FILENAMES = (".texact.toml", "texact.toml", "pyproject.toml")
_RULE_CODE_PATTERN = re.compile(r"[A-Z]{2,3}\d{3,}")


class ConfigurationError(ValueError):
    """Raised when a TeXact configuration cannot be used."""


@dataclass(frozen=True)
class LintConfig:
    """Lint settings loaded from a TeXact configuration."""

    ignore: frozenset[str] = frozenset()
    casing: tuple[str, ...] = ()
    we_count: int = 5


@dataclass(frozen=True)
class FormatConfig:
    """Output formatting settings loaded from a TeXact configuration."""

    html_style: bool = False


@dataclass(frozen=True)
class ToolsConfig:
    """External tool settings loaded from a TeXact configuration."""

    chktex_path: str | None = None


@dataclass(frozen=True)
class TexactConfig:
    """Complete, immutable TeXact configuration."""

    lint: LintConfig = field(default_factory=LintConfig)
    format: FormatConfig = field(default_factory=FormatConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    source_path: Path | None = None


def load_config(
    config_path: Path | None = None,
    directory: Path | None = None,
) -> TexactConfig:
    """Load explicit or automatically discovered TeXact configuration."""
    if config_path is not None:
        path = Path(config_path)
        if not path.is_file():
            raise ConfigurationError(f"Configuration file not found: {path}")
        config = _load_file(path)
        return config or TexactConfig(source_path=path)

    search_directory = Path.cwd() if directory is None else Path(directory)
    for filename in _CONFIG_FILENAMES:
        path = search_directory / filename
        if not path.is_file():
            continue
        config = _load_file(path)
        if config is not None:
            return config

    return TexactConfig()


def _load_file(path: Path) -> TexactConfig | None:
    try:
        with path.open("rb") as config_file:
            data = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"Invalid TOML in {path}: {error}") from error
    except OSError as error:
        raise ConfigurationError(
            f"Could not read configuration {path}: {error}"
        ) from error

    if path.name == "pyproject.toml":
        tool = data.get("tool")
        if tool is None:
            return None
        if not isinstance(tool, Mapping):
            raise ConfigurationError(f"{path}: 'tool' must be a TOML table")
        data = tool.get("texact")
        if data is None:
            return None

    if not isinstance(data, Mapping):
        raise ConfigurationError(f"{path}: configuration must be a TOML table")

    return _parse_config(data, path)


def _parse_config(data: Mapping[str, object], path: Path) -> TexactConfig:
    _check_keys(data, {"lint", "format", "tools"}, path, "")

    lint_data = _table(data.get("lint"), path, "lint")
    format_data = _table(data.get("format"), path, "format")
    tools_data = _table(data.get("tools"), path, "tools")

    _check_keys(lint_data, {"ignore", "casing", "we_count"}, path, "lint")
    _check_keys(format_data, {"html-style"}, path, "format")
    _check_keys(tools_data, {"chktex_path"}, path, "tools")

    ignore = _string_list(lint_data.get("ignore", []), path, "lint.ignore")
    invalid_codes = [code for code in ignore if not _RULE_CODE_PATTERN.fullmatch(code)]
    if invalid_codes:
        raise ConfigurationError(
            f"{path}: lint.ignore contains invalid rule code(s): "
            f"{', '.join(invalid_codes)}"
        )

    casing = _string_list(lint_data.get("casing", []), path, "lint.casing")
    we_count = lint_data.get("we_count", 5)
    if isinstance(we_count, bool) or not isinstance(we_count, int):
        raise ConfigurationError(f"{path}: lint.we_count must be an integer")
    if we_count < 0:
        raise ConfigurationError(f"{path}: lint.we_count must be non-negative")

    html_style = format_data.get("html-style", False)
    if not isinstance(html_style, bool):
        raise ConfigurationError(f"{path}: format.html-style must be a boolean")

    chktex_path = tools_data.get("chktex_path")
    if chktex_path is not None and not isinstance(chktex_path, str):
        raise ConfigurationError(f"{path}: tools.chktex_path must be a string")
    if chktex_path == "":
        raise ConfigurationError(f"{path}: tools.chktex_path must not be empty")

    return TexactConfig(
        lint=LintConfig(
            ignore=frozenset(ignore),
            casing=casing,
            we_count=we_count,
        ),
        format=FormatConfig(html_style=html_style),
        tools=ToolsConfig(chktex_path=chktex_path),
        source_path=path,
    )


def _table(
    value: object,
    path: Path,
    name: str,
) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{path}: [{name}] must be a TOML table")
    return value


def _string_list(value: object, path: Path, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path}: {name} must be an array of strings")
    if any(not isinstance(item, str) for item in value):
        raise ConfigurationError(f"{path}: {name} must be an array of strings")
    return tuple(value)


def _check_keys(
    data: Mapping[str, object],
    allowed: set[str],
    path: Path,
    section: str,
) -> None:
    for key in data:
        if key not in allowed:
            option = f"{section}.{key}" if section else key
            raise ConfigurationError(f"{path}: unsupported option '{option}'")
