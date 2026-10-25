# Pycman

Simple to use `pacman`-like progress bar for Python with zero dependencies.

> **_NOTE:_** This is inspired by [progressbar2](https://github.com/wolph/python-progressbar). If performance is crucial, consider using that package instead.

---

## Installation

You can install the package locally from source in editable mode:

```bash
pip install -e .
```

---

## Quick Start

`pycman` is designed to be used as a context manager (`PycBar`):

```python
import time
from pycman import PycBar

total_steps = 50

with PycBar(max_steps=total_steps, prefix="Loading:", color_gradient=True) as bar:
    for i in range(total_steps):
        time.sleep(0.05)
        
        # Log messages above the progress bar without breaking the UI
        if i == 25:
            bar.log("Reached halfway point!")
            
        bar.update(1)
```

---

## Examples

### 1. Multi-line Inline Logging

Output logs dynamically above the active progress bar using `bar.log()` or `bar.log_many()`. The bar safely shifts down in place without corrupting your console output.

```python
import time
from pycman import PycBar

total_steps = 50

with PycBar(max_steps=total_steps, prefix="Downloading:", color_gradient=True) as bar:
    for i in range(1, total_steps + 1):
        time.sleep(0.04)
        
        if i == 15:
            bar.log("⚡ Connected to server, fetching assets...")
        elif i == 30:
            bar.log("📦 Unpacking payload chunks...")
        elif i == 45:
            bar.log_many([
                "⚠️ Warning: Slow response detected on shard 3",
                "🔄 Retrying packet synchronization..."
            ])
            
        bar.update(1)
```

---

### 2. Custom Layout & Postfixes

Customize bar width, prefixes, postfix labels, or toggle spinner and gradient options to match your layout preferences:

```python
import time
from pycman import PycBar

total_steps = 30

with PycBar(
    max_steps=total_steps,
    bar_width=30,
    prefix="Building:",
    postfix="(modules)",
    color_gradient=False,  # Disables dynamic dynamic gradients
    show_spinner=True
) as bar:
    for _ in range(total_steps):
        time.sleep(0.06)
        bar.update(1)
```

---

### 3. Modifying Properties On-the-Fly

You can dynamically update attributes such as `prefix` and `postfix` directly on the active progress bar instance while work is in progress:

```python
import time
from pycman import PycBar

tasks = ["Compiling C++ extensions", "Running test suite", "Generating documentation"]

with PycBar(max_steps=len(tasks) * 10, prefix="Initializing...") as bar:
    for task in tasks:
        bar.prefix = f"Stage: {task}"
        for step in range(10):
            bar.postfix = f"({step + 1}/10)"
            time.sleep(0.05)
            bar.update(1)
```

---

### 4. Advanced Console Formatting with `TermMan`

`pycman` includes a terminal utility (`TermMan`) that auto-detects terminal color capabilities (TrueColor, 256-color, or Basic) and environment variables (like `NO_COLOR` or `FORCE_COLOR`):

```python
from pycman.term import TermMan

# Initialize terminal manager
term = TermMan()

print(f"Detected Color Capability Level: {term.color_level.name}")
print(f"Terminal Width: {term.width} columns")

# Format strings with Hex codes, RGB tuples, or named colors
print(term.format("✨ Success! Operation complete.", fg="#00FFCC", bold=True))
print(term.format("⚠️ Warning notice.", fg=(255, 140, 0), bg="black"))
```

---

## Features

* **Pac-Man Animation:** A fun terminal progress bar featuring a moving Pac-Man character and trailing dots.
* **TrueColor & 256-Color Support:** Automatically detects your terminal's color capabilities to render smooth color gradients.
* **Thread-Safe Background Updates:** Features a smooth spinner and elapsed/ETA calculations powered by a background thread.
* **Inline Logging:** Safely print logs above the active progress bar (`bar.log()` or `bar.log_many()`) without messing up your terminal output.
* **Zero Dependencies:** Pure standard-library Python implementation.

---

## License

[MIT](LICENSE)
