# FeastPick

**Family feast planner**: propose dishes, mark dietary tags, vote on favourites, and claim who brings what.

Share one board link. Guests join with a first name. No accounts required.

[![CI](https://github.com/letzhub/feastpick/actions/workflows/ci.yml/badge.svg)](https://github.com/letzhub/feastpick/actions/workflows/ci.yml)
[![Release](https://github.com/letzhub/feastpick/actions/workflows/release.yml/badge.svg)](https://github.com/letzhub/feastpick/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GHCR](https://img.shields.io/badge/GHCR-letzhub%2Ffeastpick-blue)](https://github.com/letzhub/feastpick/pkgs/container/feastpick)

---

## Features

- **Feast boards** with title, date, and max votes per category
- **Categories** with emoji icons + short descriptions
- **Menu options** proposed by anyone on the board
- **Dietary badges**: vegan · alcohol · fish · meat
- **Voting** (fair cap per person per category)
- **"I'll bring this"** claims
- **Live-ish board** (client polls every few seconds)
- **Demo board** seeded on first start: `/e/christmas-eve-demo`
- **Single SQLite file**: easy backups

---

## Quick start (Docker Compose)

### Requirements

- [Docker](https://docs.docker.com/get-docker/) Engine 24+
- Docker Compose v2

```bash
git clone https://github.com/letzhub/feastpick.git
cd feastpick
docker compose up -d --build
```

Open:

| | URL |
|--|-----|
| App | http://localhost:8080/ |
| Demo | http://localhost:8080/e/christmas-eve-demo |
| Health | http://localhost:8080/api/health |

The app listens on **port 8080** inside the container and on the host (same port).

Stop:

```bash
docker compose down
```

Data lives in the Docker volume `feastpick_feastpick-data` (or project-prefixed). To wipe data: `docker compose down -v`.

Published images (after a release):

```text
ghcr.io/letzhub/feastpick:1.2.0
ghcr.io/letzhub/feastpick:1.2
ghcr.io/letzhub/feastpick:latest
```

Pin a version with `FEASTPICK_VERSION` in `.env` (see `.env.example`), then `docker compose pull && docker compose up -d`.

### Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `FEASTPICK_VERSION` | `1.2.0` | Image tag / version label |
| `FEASTPICK_DATA` | `/app/data` | Data dir inside the container |
| `PORT` | `8080` | Listen port (keep 8080 unless you know you need another) |

---

## Run without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
export FEASTPICK_DATA="$(pwd)/data"
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## API (short)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Liveness + `version` |
| `GET` | `/api/meta` | Category icons + badge catalog |
| `POST` | `/api/events` | Create a feast |
| `GET` | `/api/events/{slug_or_id}` | Full board JSON |
| `POST` | `/api/events/{id}/categories` | Add category |
| `POST` | `/api/categories/{id}/options` | Add option (`tags` optional) |
| `POST` | `/api/options/{id}/vote` | Vote / unvote |
| `POST` | `/api/options/{id}/bring` | Claim / release |
| `DELETE` | `/api/options/{id}` | Delete own unclaimed option |

Interactive docs when the app is running: http://localhost:8080/docs

---

## Versioning and releases

FeastPick follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

| File | Role |
|------|------|
| [`VERSION`](VERSION) | Current version string |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |
| Git tag `vX.Y.Z` | Triggers image build + GitHub Release |

**Maintainer release checklist** is in [`CONTRIBUTING.md`](CONTRIBUTING.md).

```bash
# after updating VERSION + CHANGELOG
git add VERSION CHANGELOG.md
git commit -m "chore(release): v1.2.0"
git tag -a v1.2.0 -m "v1.2.0"
git push origin main --tags
```

The [release workflow](.github/workflows/release.yml) publishes:

- `ghcr.io/letzhub/feastpick:X.Y.Z`
- `ghcr.io/letzhub/feastpick:X.Y`
- `ghcr.io/letzhub/feastpick:X`
- `ghcr.io/letzhub/feastpick:latest`

CI on pull requests / `main` builds the image only (no push).

**First-time GHCR visibility:** after the first successful release, open  
**GitHub → Packages → feastpick → Package settings → Change visibility → Public**  
if you want anonymous pulls.

---

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, PR process, and release rules.

Security reports: **[SECURITY.md](SECURITY.md)**.

---

## Project layout

```text
app/                  FastAPI + SQLite
static/               Front-end SPA
Dockerfile            Production image
docker-compose.yml    One-command run
.github/workflows/    CI + release/GHCR
VERSION               Semver
CHANGELOG.md          Release notes
```

---

## Production tips

FeastPick is built for **trusted groups**. For a public internet deploy:

1. Put TLS in front (Caddy, Traefik, Cloudflare Tunnel, nginx)
2. Back up the SQLite volume regularly
3. Consider rate limits / CAPTCHA / access control (not built-in yet)
4. Pin the image tag (`1.2.0`) instead of `latest`

---

## License

[MIT](LICENSE) © FeastPick contributors
