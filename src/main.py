"""Flet desktop and packaged-app entry point."""

import flet as ft

from tft_builder.app import main

# Flet packaging imports the configured entry module instead of executing it as __main__.
# Keep ft.run() at module scope so both `flet run` and packaged integration tests start UI.
ft.run(main, assets_dir="assets")
