import re

ESC = "\033"
CSI = f"{ESC}["

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

RESET = f"{CSI}0m"

BOLD = f"{CSI}1m"
BOLD_OFF = f"{CSI}22m"

FG_OFF = f"{CSI}39m"
BG_OFF = f"{CSI}49m"

CLEAR_LINE = f"{CSI}2K"
CARRIAGE_RETURN = "\r"

HIDE_CURSOR = f"{CSI}?25l"
SHOW_CURSOR = f"{CSI}?25h"

NAMED = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
    "gray": 8,
}


def fg_basic(n: int) -> str:
    return f"{CSI}{30 + n}m" if n < 8 else f"{CSI}{90 + n - 8}m"


def bg_basic(n: int) -> str:
    return f"{CSI}{40 + n}m" if n < 8 else f"{CSI}{100 + n - 8}m"


def fg_256(n: int) -> str:
    return f"{CSI}38;5;{n}m"


def bg_256(n: int) -> str:
    return f"{CSI}48;5;{n}m"


def fg_rgb(r, g, b) -> str:
    return f"{CSI}38;2;{r};{g};{b}m"


def bg_rgb(r, g, b) -> str:
    return f"{CSI}48;2;{r};{g};{b}m"
