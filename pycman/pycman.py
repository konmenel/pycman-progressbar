from __future__ import annotations

import threading
import time
from collections.abc import Iterable
from enum import IntEnum

from .colors import COLORS, Color, ColorGradient
from .term import ColorLevel, TermMan


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

    @classmethod
    def parse(cls, value: str | LogLevel | None) -> LogLevel | None:
        if value is None or isinstance(value, cls):
            return value
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(
                f"Unknown log level {value!r}. Available: {[l.name for l in cls]}"
            ) from None


# (label color, bold)
LEVEL_STYLE = {
    LogLevel.DEBUG: ("gray", False),
    LogLevel.INFO: ("blue", False),
    LogLevel.WARNING: ("yellow", True),
    LogLevel.ERROR: ("red", True),
}


class PycBar:
    # DONE_CHAR = "█"
    # REMAINING_CHAR = "░"
    # REMAINING_CHAR = "▕"
    DONE_CHAR = "-"
    REMAINING_CHAR = "·"
    SPINNER_CHARS = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
    PACMAN_CHARS = ("C", "C", "C", "C", "C", "c", "c", "c", "c", "c")
    MIN_BAR_WIDTH = 10

    def __init__(
        self,
        max_steps: int,
        bar_width: int = 40,
        prefix: str = "",
        postfix: str = "",
        color_gradient: bool | ColorGradient = True,
        show_spinner: bool = True,
        term: TermMan | None = None,
        min_level: LogLevel | str = LogLevel.DEBUG,
    ):
        self.term = term or TermMan()
        self.max_steps = max(1, max_steps)
        self.width = bar_width
        self.curr_step = 0
        self.progress = 0.0

        self.show_spinner = show_spinner
        if self.term.color_level == ColorLevel.NONE:
            self._color_gradient = None
        elif isinstance(color_gradient, ColorGradient):
            self._color_gradient = color_gradient
        elif color_gradient is True:
            self._color_gradient = ColorGradient(
                COLORS["red"],
                COLORS["yellow"],
                COLORS["lime"],
            )
        else:
            self._color_gradient = None

        self._prefix = f"{prefix} " if prefix and not prefix[-1].isspace() else prefix
        self._postfix = (
            f"{postfix} " if postfix and not postfix[-1].isspace() else postfix
        )

        self.start_time = time.time()
        self.spinner_idx = 0

        self._active = False
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._animation_thread: threading.Thread | None = None
        self.min_level = LogLevel.parse(min_level)

    @property
    def prefix(self):
        return self._prefix

    @property
    def postfix(self):
        return self._postfix

    @prefix.setter
    def prefix(self, value: str):
        self._prefix = f"{value} " if value and not value[-1].isspace() else value

    @postfix.setter
    def postfix(self, value: str):
        self._postfix = f"{value} " if value and not value[-1].isspace() else value

    def __enter__(self):
        self.start_time = time.time()
        self._stop_event.clear()
        self._active = True
        if self.term.is_tty:
            self.term.hide_cursor()
            self._animation_thread = threading.Thread(
                target=self._refresh_loop, daemon=True
            )
            self._animation_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._animation_thread:
            self._animation_thread.join()
            self._animation_thread = None
        with self._lock:
            ok = exc_type is None
            if ok and self.curr_step < self.max_steps:
                self.curr_step, self.progress = self.max_steps, 1.0
            self._draw_ui(force_complete=ok)
            self.term.write("\n")
            self.term.show_cursor()
            self._active = False

    def _refresh_loop(self):
        """Runs in the background, updating the spinner frame even if the main thread is stuck."""
        while not self._stop_event.is_set():
            with self._lock:
                self._draw_ui()
                if self.show_spinner:
                    self.spinner_idx = (self.spinner_idx + 1) % len(self.SPINNER_CHARS)
            self._stop_event.wait(0.05)

    def _calculate_gradient(self) -> Color:
        if not self._color_gradient:
            return None

        return self._color_gradient.interpolate(self.progress)

    def _eta_str(self) -> str:
        if self.curr_step <= 0:
            return "--:--"
        elapsed = max(time.time() - self.start_time, 1e-9)
        steps_per_sec = self.curr_step / elapsed
        eta_seconds = (self.max_steps - self.curr_step) / steps_per_sec
        mins, secs = divmod(int(eta_seconds), 60)
        return f"{mins:02d}:{secs:02d}"

    def _build(self, bar_width: int, force_complete: bool) -> str:
        done_width = round(self.progress * bar_width)
        remain_width = max(0, bar_width - done_width)
        pacman_char = self.PACMAN_CHARS[self.spinner_idx % len(self.PACMAN_CHARS)]
        filled_bar = (
            self.DONE_CHAR * (done_width - 1) + pacman_char if done_width > 0 else ""
        )
        empty_bar = self.REMAINING_CHAR * remain_width

        color = self._calculate_gradient() if self._color_gradient else None

        spinner_str = ""
        if self.show_spinner:
            spinner_char = (
                " ✓"
                if self.curr_step >= self.max_steps or force_complete
                else " " + self.SPINNER_CHARS[self.spinner_idx]
            )
            spinner_str = self.term.format(spinner_char, fg=color)

        bar = self.term.format(filled_bar, fg=color)
        progress = self.term.format(
            f"{self.curr_step}/{self.max_steps} {self.progress: 4.0%}", fg=color
        )
        return (
            f"{self._prefix}{bar}{empty_bar}{spinner_str} {progress} "
            f"{self._postfix}(ETA: {self._eta_str()})"
        )

    def _render(self, force_complete: bool = False) -> str:
        """Build one frame as a string, shrinking the bar so it fits the terminal."""
        line = self._build(self.width, force_complete)
        if not self.term.is_tty:
            return line

        overflow = self.term.visible_len(line) - (self.term.width - 1)
        if overflow > 0:
            bar_width = max(self.MIN_BAR_WIDTH, self.width - overflow)
            line = self._build(bar_width, force_complete)
        return line

    def _draw_ui(self, force_complete: bool = False) -> None:
        """Draw the current frame in place."""
        self.term.redraw_line(self._render(force_complete))

    def update(self, increment: int = 1):
        """Update the current step.

        Parameters
        ----------
        increment : int, optional
            How many steps have passed, by default 1
        """
        with self._lock:
            self.curr_step += increment
            if self.curr_step > self.max_steps:
                self.curr_step = self.max_steps
            elif self.curr_step < 0:
                self.curr_step = 0

            self.progress = self.curr_step / self.max_steps

    def log(self, message: str, loglevel: str | LogLevel | None = None) -> None:
        self.log_many((message,), loglevel=loglevel)

    def log_many(
        self, messages: Iterable[str], loglevel: str | LogLevel | None = None
    ) -> None:
        level = LogLevel.parse(loglevel)
        if level is not None and level < self.min_level:
            return

        lines = [part for m in messages for part in (str(m).splitlines() or [""])]
        if level is not None:
            fg, bold = LEVEL_STYLE[level]
            tag = self.term.format(f"{level.name:<7}", fg=fg, bold=bold)
            lines = [f"{tag} {line}" for line in lines]

        with self._lock:
            footer = self._render() if self._active else ""
            self.term.print_above(lines, footer=footer)
