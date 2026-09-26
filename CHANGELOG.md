# Changelog

All notable changes to **FeastPick** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Optional event PIN / join gate
- Rate limiting for public deployments
- Edit dietary badges after an option is created

## [1.0.0] — 2026-03-28

First public open-source release.

### Added
- Create shared feast boards with custom categories
- Category icons and short descriptions
- Propose menu options; vote (configurable max votes per category)
- “I’ll bring this” claim on options
- Dietary / type badges on options: vegan, alcohol, fish, meat
- Live board refresh (client poll)
- Seeded Christmas Eve demo board (`/e/christmas-eve-demo`)
- SQLite persistence via Docker volume
- Docker image + `docker compose` self-host flow
- GitHub Actions: CI build + GHCR publish on version tags
- Health endpoint with app version (`GET /api/health`)

### Notes
- Identity is first-name based (localStorage) — intended for trusted groups
- No accounts, email, or encryption of board contents yet

[Unreleased]: https://github.com/OWNER/feastpick/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/OWNER/feastpick/releases/tag/v1.0.0
