from __future__ import annotations

import os
import shutil
import sys
import threading
from collections.abc import Iterable
from enum import IntEnum
from typing import TextIO, TypeAlias

from . import ansicodes
from .colors import COLORS, Color

RGB: TypeAlias = tuple[int, int, int]


class ColorLevel(IntEnum):
    NONE = 0
    BASIC = 1
    ANSI256 = 2
    TRUECOLOR = 3


class TermMan:
    def __init__(
        self, stream: TextIO | None = None, color_level: ColorLevel | None = None
    ):
        self.stream = stream or sys.stdout
        self.lock = threading.RLock()
        self._enable_windows_vt()
        self.color_level = (
            self._detect_color_level() if color_level is None else color_level
        )

    # ---------- capability detection ----------
    @property
    def is_tty(self) -> bool:
        isatty = getattr(self.stream, "isatty", None)
        try:
            return bool(isatty()) if isatty else False
        except (ValueError, OSError):  # closed stream
            return False

    @staticmethod
    def _enable_windows_vt() -> None:
        """Older Windows consoles need this once to interpret ANSI sequences."""
        if os.name == "nt":
            os.system("")

    def _detect_color_level(self) -> ColorLevel:
        env = os.environ
        if "NO_COLOR" in env:
            return ColorLevel.NONE
        forced = bool(env.get("FORCE_COLOR"))
        if not forced and not self.is_tty:
            return ColorLevel.NONE
        term = env.get("TERM", "").lower()
        if term == "dumb":
            return ColorLevel.NONE
        if env.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
            return ColorLevel.TRUECOLOR
        if "256color" in term:
            return ColorLevel.ANSI256
        return ColorLevel.BASIC if (term or forced) else ColorLevel.NONE

    @property
    def width(self) -> int:
        """Width of *this* stream's terminal (not necessarily sys.stdout's)."""
        try:
            columns = os.get_terminal_size(self.stream.fileno()).columns
        except (AttributeError, ValueError, OSError):
            columns = 0
        # Some ptys/consoles report 0 columns until a size is set.
        return columns if columns > 0 else shutil.get_terminal_size((80, 24)).columns

    @staticmethod
    def visible_len(text: str) -> int:
        """Length of text as displayed, ignoring ANSI escape sequences."""
        return len(ansicodes.ANSI_RE.sub("", text))

    # ---------- color resolution ----------
    @staticmethod
    def _to_color(color: Color | str | RGB) -> Color:
        if isinstance(color, Color):
            return color
        if isinstance(color, tuple):
            return Color(*color)
        if color.startswith("#") and len(color) == 7:
            try:
                rgb = (int(color[i : i + 2], 16) for i in (1, 3, 5))
            except ValueError:
                raise ValueError(f"Invalid hex color {color!r}") from None
            return Color(*rgb)
        try:
            return COLORS[color.lower()]
        except KeyError:
            raise ValueError(
                f"Unknown color {color!r}. Available: {sorted(COLORS)}"
            ) from None

    @staticmethod
    def _rgb_to_256(color: Color) -> int:
        r, g, b = color.red, color.green, color.blue
        if r == g == b:  # grayscale ramp
            if r < 8:
                return 16
            if r > 248:
                return 231
            return 232 + round((r - 8) / 247 * 24)
        return (
            16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)
        )

    @staticmethod
    def _rgb_to_basic(color: Color) -> int:
        r, g, b = color.red, color.green, color.blue
        bright = max(r, g, b) > 170
        idx = (r > 127) | ((g > 127) << 1) | ((b > 127) << 2)
        return idx + (8 if bright and idx else 0)

    def _color_seq(self, color: Color, *, background: bool) -> str:
        if self.color_level is ColorLevel.NONE:
            return ""
        value = self._to_color(color)
        basic, c256, rgb = (
            (ansicodes.bg_basic, ansicodes.bg_256, ansicodes.bg_rgb)
            if background
            else (ansicodes.fg_basic, ansicodes.fg_256, ansicodes.fg_rgb)
        )
        if self.color_level is ColorLevel.TRUECOLOR:
            return rgb(*value)
        if self.color_level is ColorLevel.ANSI256:
            return c256(self._rgb_to_256(*value))
        return basic(self._rgb_to_basic(*value))

    # ---------- formatting ----------
    def format(
        self,
        text: str,
        *,
        fg: Color | None = None,
        bg: Color | None = None,
        bold: bool = False,
    ) -> str:
        if self.color_level is ColorLevel.NONE:
            return text
        start, end = "", ""
        if bold:
            start += ansicodes.BOLD
            end = ansicodes.BOLD_OFF + end
        if bg is not None:
            start += self._color_seq(bg, background=True)
            end = ansicodes.BG_OFF + end
        if fg is not None:
            start += self._color_seq(fg, background=False)
            end = ansicodes.FG_OFF + end
        return f"{start}{text}{end}" if start else text

    # ---------- output ----------
    def write(self, text: str) -> None:
        with self.lock:
            self.stream.write(text)
            self.stream.flush()

    def hide_cursor(self) -> None:
        if self.is_tty:
            self.write(ansicodes.HIDE_CURSOR)

    def show_cursor(self) -> None:
        if self.is_tty:
            self.write(ansicodes.SHOW_CURSOR)

    def redraw_line(self, text: str) -> None:
        if self.is_tty:
            self.write(f"{ansicodes.CARRIAGE_RETURN}{ansicodes.CLEAR_LINE}{text}")
        else:
            self.write(text)

    def print_above(self, lines: Iterable[str], footer: str = "") -> None:
        """Print lines above a live footer (e.g. a progress bar) in a single write.

        On a non-TTY the footer is dropped: redrawing it would only spam logs.
        """
        body = "".join(f"{line}\n" for line in lines)
        if self.is_tty:
            self.write(
                f"{ansicodes.CARRIAGE_RETURN}{ansicodes.CLEAR_LINE}{body}{footer}"
            )
        else:
            self.write(body)
