import re

from reviewer import Reviewer, Status
from printer import Printer


class Reviewer_Casing(Reviewer):
    # Canonical spellings to enforce
    CORRECT_SPELLINGS = (
        "ASIC",
        "CMOS",
        "CORDIC",
        "FPGA",
        "VLSI",
        "FloPoCo",
        "RTL",
        "HDL",
        "FSM",
        "DNN",
        "CNN",
        "ReLU",
        "PWL",
        "RAM",
        "RMS",
        "Verilog",
        "SystemVerilog",
        "VHDL",
        "FIR",
        "IIR",
        "LWDF",
        # "AXI", # collides with the word axis
        "SRAM",
        "DSP",
        "FIFO",
        "ALU",
        "PDK",
        "PLL",
        "HLS",
        "AI",
        "ML",
        "AMD",
        "Intel",
        "Xilinx",
        "Altera",
        "Lattice",
        "LSTM",
        "TSMC",
        "FD-SOI",
        "Synopsys",
        "Cadence",
        "Vivado",
        "Quartus",
        "APyTypes",
        "URL",
        "DNS",
        "BRAM",
        "DRAM",
        "NaN",
        "LUT",
        "LNS",
        "MNIST",
        "MHz",
        "kHz",
        "GHz",
        "Basys",
        "Virtex",
        "Spartan",
    )
    _PATTERN_LATEX_IGNORED_COMMANDS = re.compile(
        r"\\(?:cite|ref|label|url|usepackage)\{[^}]*\}"
    )

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.comments: list[tuple[int, str]] = []
        self.mismatch_count = 0

    def process_line(self, line_no: int, line: str) -> None:
        # Remove comments (everything after %)
        if "%" in line:
            line = line[: line.index("%")]

        # Ignore casing checks inside \cite{...}, \ref{...}, \label{...}, and \url{...}
        line = self._PATTERN_LATEX_IGNORED_COMMANDS.sub("", line)

        # Check each word in the line
        for correct_spelling in self.CORRECT_SPELLINGS:
            word_lower = correct_spelling.lower()
            # Create regex pattern to match the word with optional suffixes:
            # - plural 's': fpgas
            # - possessive 's: fpga's
            # - colon suffix: fpga:s
            # - hyphenated compounds: fpga-design
            pattern = re.compile(
                r"(?<![a-zA-Z])(?P<base>"
                + re.escape(word_lower)
                + r")(?P<suffix>s|'s|:s)?(?=\W|$)",
                re.IGNORECASE,
            )

            for match in pattern.finditer(line):
                matched_text = match.group(0)
                matched_base = match.group("base")
                matched_suffix = match.group("suffix") or ""
                normalized_suffix = matched_suffix.lower()
                expected_text = f"{correct_spelling}{normalized_suffix}"
                if matched_base != correct_spelling:
                    self.comments.append(
                        (
                            line_no,
                            f"Incorrect casing: {self.printer.dark_red(matched_text)} should be {self.printer.yellow(expected_text)}",
                        )
                    )
                    self.mismatch_count += 1

    def get_comments(self) -> list[tuple[int, str]]:
        return self.comments

    def get_summary(self) -> str:
        if self.mismatch_count == 0:
            return ""
        return f"Casing errors: {self.mismatch_count}"

    def get_status(self) -> Status:
        return Status.PASSED if self.mismatch_count == 0 else Status.FAILED

    def get_name(self) -> str:
        return "Casing"
