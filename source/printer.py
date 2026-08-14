"""Class for printing output."""

from typing import TYPE_CHECKING

from colorama import Fore, Style, init as colorama_init

if TYPE_CHECKING:  # Only for type hints
    from reviewers.reviewer import Diagnostic, Status


class Printer:
    """Formats TeXact output for terminal or HTML display."""

    GREEN = Fore.GREEN
    DARK_RED = Fore.RED
    YELLOW = Fore.YELLOW
    RESET = Style.RESET_ALL
    HTML_GREEN = "#008000"
    HTML_DARK_RED = "#800000"
    HTML_YELLOW = "#808000"

    def __init__(self, html_style: bool = False) -> None:
        self.html_style = html_style
        if not self.html_style:
            colorama_init()

    def print(self, message: str) -> None:
        if self.html_style:
            print(f"{message}<br>")
        else:
            print(message)

    def print_no(self, line_no: int, warning_number: int, message: str) -> None:
        line_label = f"L{line_no + 1}:"
        warning_label = f"[{warning_number}]"
        if self.html_style:
            print(
                f"{self.green(line_label)} {self.yellow(warning_label)} {message}<br>"
            )
        else:
            print(f"{self.green(line_label)} {self.yellow(warning_label)} {message}")

    def print_diagnostic(self, diagnostic: "Diagnostic") -> None:
        line_label = self.green(f"L{diagnostic.line}")
        warning_label = self.dark_red(f"[{diagnostic.code}]")
        message = f"{line_label} {warning_label}: {diagnostic.message}"
        if self.html_style:
            print(f"{message}<br>")
        else:
            print(message)

    def green(self, message: str) -> str:
        if self.html_style:
            return self.html_color(message, self.HTML_GREEN)
        return f"{self.GREEN}{message}{self.RESET}"

    def yellow(self, message: str) -> str:
        if self.html_style:
            return self.html_color(message, self.HTML_YELLOW)
        return f"{self.YELLOW}{message}{self.RESET}"

    def dark_red(self, message: str) -> str:
        if self.html_style:
            return self.html_color(message, self.HTML_DARK_RED)
        return f"{self.DARK_RED}{message}{self.RESET}"

    def html_color(self, text: str, color: str) -> str:
        return f'<span style="color:{color}">{text}</span>'

    def status_str(self, status: "Status") -> str:
        name = getattr(status, "name", str(status))
        if name == "PASSED":
            return self.green(name)
        elif name == "FAILED":
            return self.dark_red(name)
        else:
            return self.yellow(name)
