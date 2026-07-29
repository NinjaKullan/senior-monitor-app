"""Make `kettle` and `scripts` importable when pytest runs from the repo root."""

from __future__ import annotations

import sys
from pathlib import Path

PRODUCT_ROOT = str(Path(__file__).resolve().parent)
if PRODUCT_ROOT not in sys.path:
    sys.path.insert(0, PRODUCT_ROOT)
