import re
from enum import Enum, auto
from pathlib import Path


class Template(Enum):
    """Document templates recognized by TeXact."""

    IEEE = auto()
    LLNCS = auto()
    UNKNOWN = auto()


_PATTERN_DOCUMENTCLASS = re.compile(
    r"\\documentclass(?:\[[^\]]*\])?\{(?P<class_name>[^}]*)\}"
)


def get_template(latex_file: str | Path) -> Template:
    file_path = Path(latex_file)
    with file_path.open("r", encoding="utf-8") as input_file:
        for line in input_file:
            line_without_comments = line.split("%", 1)[0]
            if not line_without_comments.strip():
                continue

            match = _PATTERN_DOCUMENTCLASS.search(line_without_comments)
            if match is None:
                continue

            class_name = match.group("class_name").strip().lower()
            if class_name == "ieeetran":
                return Template.IEEE
            if class_name == "llncs":
                return Template.LLNCS
            return Template.UNKNOWN
