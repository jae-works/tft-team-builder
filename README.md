# TFT Team Builder

Current state: planning baseline v0.0.4 only. No application code has been implemented yet.

Persistent project documents:
- `PROJECT_CONTEXT.md`: mandatory handoff/orientation for another developer or AI instance.
- `REQUIREMENTS.md`: what the application must eventually satisfy.
- `PROGRESS.md`: what is actually implemented and verified in the current version.
- `IMPLEMENTATION_BLOCKS.md`: the current nine-block high-level roadmap and block status.
- `DEVELOPMENT_PLAN.md`: development/delivery rules and current implementation order.
- `SET_DATA_PIPELINE.md`: binding plan for sourcing, generating and validating TFT Set data/assets.
- `sets/README.md`: rules for generated runtime Set packages.
- `set_sources/README.md`: rules for project-owned overrides/source decisions.

Every future coding delivery must include the entire current project plus these documents and a SHA-256 checksum for the ZIP. Later implementation blocks may be adjusted after completed blocks when real implementation findings justify the change; the change must be documented. The final Windows package must also include the core project documents in a readable `project_docs/` directory next to the application.

The normal application is planned to run entirely from local validated Set packages. Riot Data Dragon is the preferred official source for supported visible assets/localized data; CommunityDragon is supplemental build-time input only where richer TFT metadata is needed. Exact source versions/provenance are recorded so Set packages are reproducible and auditable.


Engineering baseline: project-owned code, identifiers, paths, comments and technical documentation are English and use simple ASCII punctuation. Runtime writable paths are centralized and platform-aware rather than dependent on the current working directory. Dependencies are selected from current maintained libraries when they provide concrete value and are configured centrally in `pyproject.toml` once implementation begins.
