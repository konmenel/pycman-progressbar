# Pycman
Simple to use `pacman`-like progress bar for Python with zero dependencies.

> **_NOTE:_** This is inpired by [progressbar2](https://github.com/wolph/python-progressbar). If performance is crucial, consider using that package instead.


---

## Installation

You can install the package locally from source in editable mode:

```bash
pip install -e .


---

## Quick Start

`pycman` is designed to be used easily as a context manager:

```python
import time
from pycman import ProgressBar

total_steps = 50

with ProgressBar(max_steps=total_steps, prefix="Loading:", color_gradient=True) as pb:
    for i in range(total_steps):
        time.sleep(0.05)
        
        # Log messages above the progress bar without breaking the UI
        if i == 25:
            pb.log("Reached halfway point!")
            
        pb.update(1)

```

---

## Features

* **Pac-Man Animation:** A fun terminal progress bar featuring a moving Pac-Man character and trailing dots.
* **TrueColor & 256-Color Support:** Automatically detects your terminal's color capabilities to render smooth color gradients.
* **Thread-Safe Background Updates:** Features a smooth spinner and elapsed/ETA calculations powered by a background thread.
* **Inline Logging:** Safely print logs above the active progress bar (`pb.log()` or `pb.log_many()`) without messing up your terminal output.

---

## License

[MIT](LICENSE)
