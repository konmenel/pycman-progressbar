from __future__ import annotations

from typing import TypeAlias

RGB: TypeAlias = tuple[int, int, int]


class Color:
    # TODO: Add initialisers from hex or names
    __slots__ = ("blue", "green", "red")

    red: int
    green: int
    blue: int

    def __init__(self, r, g, b):
        self.red = r
        self.green = g
        self.blue = b

    def __iter__(self):
        """Allows unpacking (r, g, b = color) and conversion to list/tuple."""
        yield self.red
        yield self.green
        yield self.blue

    def __getitem__(self, index: int) -> int:
        """Allows index-based access (color[0] for red, etc.)."""
        if index == 0:
            return self.red
        elif index == 1:
            return self.green
        elif index == 2:
            return self.blue
        raise IndexError("Color index out of range (valid indices: 0, 1, 2)")

    def __add__(self, other: Color) -> Color:
        return Color(
            self.red + other.red, self.green + other.green, self.blue + other.blue
        )

    def __sub__(self, other: Color) -> Color:
        return Color(
            self.red - other.red, self.green - other.green, self.blue - other.blue
        )

    def __mul__(self, scalar: float) -> Color:
        return Color(
            int(self.red * scalar), int(self.green * scalar), int(self.blue * scalar)
        )

    def __rmul__(self, scalar: float) -> Color:
        return self.__mul__(scalar)

    def __repr__(self) -> str:
        return f"Color(r={self.red}, g={self.green}, b={self.blue})"


COLORS = {
    # Basic / ANSI-aligned colors
    "black": Color(0, 0, 0),
    "white": Color(255, 255, 255),
    "red": Color(255, 0, 0),
    "green": Color(0, 128, 0),
    "blue": Color(0, 0, 255),
    "yellow": Color(255, 255, 0),
    "magenta": Color(255, 0, 255),
    "cyan": Color(0, 255, 255),
    "gray": Color(128, 128, 128),
    "dark_gray": Color(64, 64, 64),
    # Extended popular colors
    "orange": Color(255, 165, 0),
    "purple": Color(128, 0, 128),
    "pink": Color(255, 192, 203),
    "brown": Color(165, 42, 42),
    "navy": Color(0, 0, 128),
    "teal": Color(0, 128, 128),
    "maroon": Color(128, 0, 0),
    "olive": Color(128, 128, 0),
    "bright_green": Color(0, 255, 0),
    "lime": Color(0, 255, 0),
    "gold": Color(255, 215, 0),
    "coral": Color(255, 127, 80),
    "crimson": Color(220, 20, 60),
    "indigo": Color(75, 0, 130),
    "turquoise": Color(64, 224, 208),
    "violet": Color(238, 130, 238),
}


class ColorGradient:
    def __init__(self, *colors: Color):
        self.colors = list(colors)
        if not self.colors:
            raise ValueError("ColorGradient requires at least one color.")

    def interpolate(self, progress: float) -> Color:
        """Fast linear interpolation (lerp) across multiple color stops.
        progress should be a float between 0.0 and 1.0.
        """
        if len(self.colors) == 1 or progress <= 0.0:
            return self.colors[0]
        if progress >= 1.0:
            return self.colors[-1]

        # Scale progress to the number of gradient segments
        scaled_progress = progress * (len(self.colors) - 1)
        idx = int(scaled_progress)
        t = scaled_progress - idx

        if idx >= len(self.colors) - 1:
            return self.colors[-1]

        c1 = self.colors[idx]
        c2 = self.colors[idx + 1]

        diff = c2 - c1
        return c1 + (diff * t)
