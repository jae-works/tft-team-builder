"""Small project-wide constants.

This module intentionally contains only values that are stable across the application.
Runtime configuration belongs in dedicated configuration objects instead of growing this
file into an unstructured global settings module.
"""

from __future__ import annotations

APP_NAME = "TFT Team Builder"
APP_SLUG = "tft-team-builder"
APP_AUTHOR = "TFT Team Builder"
APP_VERSION = "0.1.0"
SET_SCHEMA_VERSION = 1
SOURCE_SPEC_SCHEMA_VERSION = 1
SOURCE_MANIFEST_SCHEMA_VERSION = 1
DEFAULT_LOCALE = "en"

TECHNICAL_TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
