# Set data

Every TFT set lives in its own directory under this folder.

The application will not assume that a folder is valid simply because it exists. A Set loader/validator will check completeness before making a Set selectable.

Planned minimum checks include:
- manifest exists and has a supported schema version;
- required data files exist;
- set_id is present and stable;
- champion IDs are unique;
- trait IDs are unique;
- every champion trait reference points to a real trait;
- dynamic trait references point to real traits and use supported selection modes;
- trait breakpoints are valid and ordered;
- display ordering is deterministic;
- required champion and trait assets exist or an explicitly supported fallback is configured;
- Team Planner codec/config references are known to the application;
- locale data can fall back safely to English;
- no executable Python files are loaded from Set packages.

A detailed machine-readable schema and a real bundled development Set will be added in Step 1.
