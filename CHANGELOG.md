# Changelog

All notable changes to **FeastPick** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Optional event PIN / join gate
- Rate limiting for public deployments
- Edit dietary badges after an option is created
- Custom colours beyond preset themes
- CSV export of bring list

## [1.2.0] - 2026-09-27

### Added
- **Event colour themes** (classic, Christmas, Halloween, Easter, Thanksgiving, New Year, Valentine, Summer)
- Theme picker on create only (theme locked after create; board still applies it)
- **Print** board action with print-friendly layout: selections, votes, who chose, who brings what
- **Share** board action: copy link to clipboard + toast
- Random feast title generator on create, with Shuffle
- `ROADMAP.md` for planned work after local testing

### Changed
- Create form date defaults to **today** (local calendar)
- Board header: Share and Print on the right (no full-width link field)

## [1.1.0] - 2026-09-26

### Changed
- Default listen port is **8080** inside the container and on the host (same port; no more 3011)
- Image name fixed to `ghcr.io/letzhub/feastpick` (no `GHCR_OWNER` override)
- Base image: `python:3.13-alpine`
- Dependencies updated to current PyPI: FastAPI 0.141.1, uvicorn 0.54.0, pydantic 2.13.5
- Dockerfile build args default to release-oriented values (`VERSION=1.1.0`, `VCS_REF=local`)
- README simplified: single compose quick start

### Removed
- `GHCR_OWNER` env and dual “Option B” pull docs

## [1.0.0] - 2026-03-28

First public open-source release.

### Added
- Create shared feast boards with custom categories
- Category icons and short descriptions
- Propose menu options; vote (configurable max votes per category)
- "I'll bring this" claim on options
- Dietary / type badges on options: vegan, alcohol, fish, meat
- Live board refresh (client poll)
- Seeded Christmas Eve demo board (`/e/christmas-eve-demo`)
- SQLite persistence via Docker volume
- Docker Compose + GHCR image packaging
- MIT license

[Unreleased]: https://github.com/letzhub/feastpick/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/letzhub/feastpick/releases/tag/v1.2.0
[1.1.0]: https://github.com/letzhub/feastpick/releases/tag/v1.1.0
[1.0.0]: https://github.com/letzhub/feastpick/releases/tag/v1.0.0
