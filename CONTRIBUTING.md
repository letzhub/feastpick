# Contributing to FeastPick

Thanks for helping improve FeastPick. Small, focused contributions are welcome.

## Ways to contribute

- **Bug reports** — use a GitHub Issue; include steps, browser/OS, and FeastPick version (`/api/health`)
- **Feature ideas** — open an Issue first so we can discuss scope
- **Code / docs** — fork → branch → pull request
- **Translations / accessibility** — very welcome

## Development setup

### Prerequisites

- Docker (recommended), **or**
- Python 3.12+, and `pip`

### Run with Docker Compose (recommended)

```bash
git clone https://github.com/OWNER/feastpick.git
cd feastpick
docker compose up -d --build
```

App: http://localhost:3011/  
Demo: http://localhost:3011/e/christmas-eve-demo  
Health: http://localhost:3011/api/health

### Run without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FEASTPICK_DATA="$(pwd)/data"
mkdir -p data
uvicorn app.main:app --reload --host 0.0.0.0 --port 3011
```

## Project layout

```
app/           FastAPI backend + SQLite helpers
static/        SPA (HTML/CSS/JS)
Dockerfile     Production image
docker-compose.yml
VERSION        Semver source of truth (keep in sync with tags)
CHANGELOG.md   Human-readable release notes
```

## Coding guidelines

- Keep the stack simple: FastAPI + SQLite + static front-end (no heavy SPA framework unless discussed)
- Prefer small PRs (one concern per PR)
- Match existing style; avoid drive-by refactors
- Do not commit real user data, secrets, or local `data/*.db`
- User-facing strings: clear, friendly English
- New API fields should remain backward-compatible when possible

## Tests / checks before a PR

```bash
# Build image
docker compose build

# Smoke test
docker compose up -d
curl -fsS http://127.0.0.1:3011/api/health
curl -fsS http://127.0.0.1:3011/api/meta | head
docker compose down
```

If you change Python deps, pin versions in `requirements.txt`.

## Pull requests

1. Fork the repo and create a branch: `git checkout -b feature/short-name`
2. Update `CHANGELOG.md` under **[Unreleased]** when the change is user-visible
3. Open a PR against `main` and fill in the template
4. Link related issues (`Fixes #123`)

Maintainers may ask for small tweaks; that’s normal.

## Versioning & releases (maintainers)

We use [Semantic Versioning](https://semver.org/):

| Change | Bump |
|--------|------|
| Bug fix, docs, internal | `PATCH` (1.0.x) |
| New feature, backward compatible | `MINOR` (1.x.0) |
| Breaking API / data migration | `MAJOR` (x.0.0) |

Release flow:

1. Move items from **[Unreleased]** into a new section in `CHANGELOG.md`
2. Set `VERSION` to the new version (e.g. `1.1.0`)
3. Commit: `chore(release): v1.1.0`
4. Tag and push:

   ```bash
   git tag -a v1.1.0 -m "v1.1.0"
   git push origin main --tags
   ```

5. GitHub Actions builds the image and publishes:
   - `ghcr.io/<owner>/feastpick:1.1.0`
   - `ghcr.io/<owner>/feastpick:1.1`
   - `ghcr.io/<owner>/feastpick:latest`
6. A GitHub Release is created from the tag (notes from CHANGELOG / generated notes)

## Code of conduct

Be respectful. No harassment, spam, or bad-faith contributions. Maintainers may close issues/PRs that don’t meet that bar.

## License

By contributing, you agree your contributions are licensed under the MIT License (see `LICENSE`).
