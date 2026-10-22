import os
import sys
import threading
import time
from collections.abc import Iterable


class ProgressBar:
    RESET = "\033[0m"
    RESET_BOLD = "\033[22m"
    BOLD = "\033[1m"
    GRAY = "\033[90m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    # DONE_CHAR = "█"
    # REMAINING_CHAR = "░"
    # REMAINING_CHAR = "▕"
    DONE_CHAR = "-"
    REMAINING_CHAR = "·"
    SPINNER_CHARS = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
    PACMAN_CHARS = ("C", "C", "C", "C", "C", "c", "c", "c", "c", "c")

    def __init__(
        self,
        max_steps: int,
        bar_width: int = 40,
        prefix: str = "",
        postfix: str = "",
        color_gradient: bool = True,
        show_spinner: bool = True,
    ):
        self.max_steps = max(1, max_steps)
        self.width = bar_width
        self.curr_step = 0
        self.progress = 0.0
        self.color_gradient = color_gradient
        self.show_spinner = show_spinner
        self._prefix = f"{prefix} " if prefix and not prefix[-1].isspace() else prefix
        self._postfix = (
            f"{postfix} " if postfix and not postfix[-1].isspace() else postfix
        )

        self.start_time = time.time()
        self.spinner_idx = 0

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._animation_thread = None

        self.supports_truecolor = os.environ.get("COLORTERM", "").lower() in (
            "truecolor",
            "24bit",
        )

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

        self._animation_thread = threading.Thread(
            target=self._refresh_loop, daemon=True
        )
        self._animation_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._animation_thread:
            self._animation_thread.join()

        with self._lock:
            if self.curr_step < self.max_steps and exc_type is None:
                self.curr_step = self.max_steps
                self.progress = 1.0

            self._draw_ui(force_complete=(exc_type is None))
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _refresh_loop(self):
        """Runs in the background, updating the spinner frame even if the main thread is stuck."""
        while not self._stop_event.is_set():
            with self._lock:
                self._draw_ui()
                if self.show_spinner:
                    self.spinner_idx = (self.spinner_idx + 1) % len(self.SPINNER_CHARS)
            time.sleep(0.05)

    def get_gradient_color(self) -> str:
        if self.progress < 0.5:
            fraction = self.progress / 0.5
            r = 255
            g = int(fraction * 255)
            b = 0
        else:
            fraction = (self.progress - 0.5) / 0.5
            r = int((1.0 - fraction) * 255)
            g = 255
            b = 0

        if self.supports_truecolor:
            return f"\033[38;2;{r};{g};{b}m"
        else:
            r_idx = int(r / 255 * 5)
            g_idx = int(g / 255 * 5)
            b_idx = int(b / 255 * 5)
            color_id = 16 + (36 * r_idx) + (6 * g_idx) + b_idx
            return f"\033[38;5;{color_id}m"

    def _draw_ui(self, force_complete: bool = False):
        """Internal low-level render function."""
        done_width = round(self.progress * self.width)
        remain_width = max(0, self.width - done_width)

        if self.color_gradient:
            color = self.get_gradient_color()
            reset = self.RESET
            # gray = self.GRAY
        else:
            color = ""
            reset = ""
            # gray = ""

        pacman_char = self.PACMAN_CHARS[self.spinner_idx % len(self.PACMAN_CHARS)]
        if done_width > 0:
            filled_bar = self.DONE_CHAR * (done_width - 1) + pacman_char
        else:
            filled_bar = ""

        empty_bar = self.REMAINING_CHAR * remain_width

        elapsed = time.time() - self.start_time

        if self.curr_step > 0:
            steps_per_sec = self.curr_step / elapsed
            remaining_steps = self.max_steps - self.curr_step
            eta_seconds = remaining_steps / steps_per_sec
            mins, secs = divmod(int(eta_seconds), 60)
            eta_str = f"{mins:02d}:{secs:02d}"
        else:
            eta_str = "--:--"

        spinner_str = ""
        if self.show_spinner:
            if self.curr_step >= self.max_steps or force_complete:
                spinner_str = f"{color}✓{reset} "
            else:
                char = self.SPINNER_CHARS[self.spinner_idx]
                spinner_str = f"{color}{char}{reset} "

        out_str = (
            f"\r\033[K{self._prefix}"
            # f"{color}{filled_bar}{gray}{empty_bar}{reset}"
            f"{color}{filled_bar}{reset}{empty_bar}"
            f" {spinner_str}"
            f" {color}{self.curr_step}/{self.max_steps} {self.progress: 4.0%}{reset}"
            f" {self._postfix}(ETA: {eta_str})"
        )
        sys.stdout.write(out_str)
        sys.stdout.flush()

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

    def log(self, message: str):
        """Prints a log message above the active progress bar

        Parameters
        ----------
        message : str
            The message to be printed
        """
        with self._lock:
            sys.stdout.write("\r\033[K")
            sys.stdout.write(f"{message}\n")
            self._draw_ui()

    def log_many(self, messages: Iterable[str]) -> None:
        """Prints multiple log messages above the active progress bar.

        Parameters
        ----------
        messages : Iterable[str]
            A collection or generator of messages to be printed.
        """
        with self._lock:
            sys.stdout.write("\r\033[K")
            for message in messages:
                sys.stdout.write(f"{message}\n")
            self._draw_ui()
