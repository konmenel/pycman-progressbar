from __future__ import annotations

import io
import time

import pytest

from pycman.ansicodes import ANSI_RE
from pycman.pycman import PycBar
from pycman.term import ColorLevel, TermMan


def test_ansicodes_regex():
    """Verify that ANSI_RE correctly strips escape codes."""
    sample = "\033[31mHello\033[0m \033[1mWorld\033[22m"
    cleaned = ANSI_RE.sub("", sample)
    assert cleaned == "Hello World"


def test_term_man_color_levels():
    """Test TermMan detection and basic formatting with NONE color level."""
    stream = io.StringIO()
    term = TermMan(stream=stream, color_level=ColorLevel.NONE)

    assert term.color_level == ColorLevel.NONE
    formatted = term.format("test", fg="red", bold=True)
    # When color level is NONE, format should return raw text unchanged
    assert formatted == "test"


def test_term_man_truecolor_formatting():
    """Test formatting with truecolor enabled."""
    stream = io.StringIO()
    term = TermMan(stream=stream, color_level=ColorLevel.TRUECOLOR)

    # Test named color
    seq_red = term._color_seq("red", background=False)
    assert (
        "38;5;" not in seq_red
    )  # Should use truecolor or basic depending on implementation, but for truecolor named uses basic/rgb mapped? Wait, named maps to int in basic. Let's test RGB tuple / hex.

    # Test hex color
    seq_hex = term._color_seq("#ff8800", background=False)
    assert "38;2;255;136;0" in seq_hex


def test_pycbar_context_manager():
    """Test basic usage of PycBar context manager on a non-TTY stream (so it doesn't spam stdout)."""
    stream = io.StringIO()
    term = TermMan(stream=stream, color_level=ColorLevel.NONE)

    max_steps = 5
    with PycBar(
        max_steps=max_steps, bar_width=10, term=term, show_spinner=False
    ) as bar:
        for _ in range(max_steps):
            bar.update(1)
            time.sleep(0.01)

    output = stream.getvalue()
    # Ensure progress reached completion
    assert "5/5" in output
    assert "100%" in output


def test_pycbar_logging():
    """Test log messages printed above the progress bar."""
    stream = io.StringIO()
    term = TermMan(stream=stream, color_level=ColorLevel.NONE)

    with PycBar(max_steps=3, bar_width=10, term=term, show_spinner=False) as bar:
        bar.update(1)
        bar.log("Status update 1")
        bar.update(1)
        bar.log_many(["Status update 2", "Status update 3"])

    output = stream.getvalue()
    assert "Status update 1" in output
    assert "Status update 2" in output
    assert "Status update 3" in output
