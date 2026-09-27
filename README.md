# TFT Team Builder

Current state: planning baseline v0.0.2 only. No application code has been implemented yet.

Persistent project documents:
- `PROJECT_CONTEXT.md`: mandatory handoff/orientation for another developer or AI instance.
- `REQUIREMENTS.md`: what the application must eventually satisfy.
- `PROGRESS.md`: what is actually implemented and verified in the current version.
- `DEVELOPMENT_PLAN.md`: the larger implementation steps.
- `SET_DATA_PIPELINE.md`: binding plan for sourcing, generating and validating TFT Set data/assets.
- `sets/README.md`: rules for generated runtime Set packages.
- `set_sources/README.md`: rules for project-owned overrides/source decisions.

Every future coding delivery must include the entire current project plus these documents and a SHA-256 checksum for the ZIP. The final Windows package must also include the core project documents in a readable `project_docs/` directory next to the application.

The normal application is planned to run entirely from local validated Set packages. Riot Data Dragon is the preferred official source for supported visible assets/localized data; CommunityDragon is supplemental build-time input only where richer TFT metadata is needed. Exact source versions/provenance are recorded so Set packages are reproducible and auditable.
