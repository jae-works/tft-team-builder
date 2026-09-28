"""Isolate packaged Flet integration tests from normal user application data."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_RUNTIME = Path(__file__).resolve().parent / ".runtime"
shutil.rmtree(_RUNTIME, ignore_errors=True)
_RUNTIME.mkdir(parents=True)
os.environ["TFT_BUILDER_DATA_DIR"] = str(_RUNTIME)
