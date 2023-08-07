import os
import sys
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def suppress_stdout() -> Iterator[None]:
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
