# FeastPick

**Family feast planner** - propose dishes, mark dietary tags, vote on favourites, and claim who brings what.

Share one board link. Guests join with a first name. No accounts required.

[![CI](https://github.com/letzhub/feastpick/actions/workflows/ci.yml/badge.svg)](https://github.com/letzhub/feastpick/actions/workflows/ci.yml)
[![Release](https://github.com/letzhub/feastpick/actions/workflows/release.yml/badge.svg)](https://github.com/letzhub/feastpick/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GHCR](https://img.shields.io/badge/GHCR-feastpick-blue)](https://github.com/letzhub/feastpick/pkgs/container/feastpick)

---

## Features

- **Feast boards** with title, date, and max votes per category
- **Categories** with emoji icons + short descriptions
- **Menu options** proposed by anyone on the board
- **Dietary badges**: vegan · alcohol · fish · meat
- **Voting** (fair cap per person per category)
- **“I’ll bring this”** claims
- **Live-ish board** (client polls every few seconds)
- **Demo board** seeded on first start: `/e/christmas-eve-demo`
- **Single SQLite file** - easy backups

---

## Quick start (Docker Compose)

### Requirements

- [Docker](https://docs.docker.com/get-docker/) Engine 24+
- Docker Compose v2

### Option A - build from source

```bash
git clone https://github.com/letzhub/feastpick.git
cd feastpick
docker compose up -d --build
```

Open:

| | URL |
|--|-----|
| App | http://localhost:3011/ |
| Demo | http://localhost:3011/e/christmas-eve-demo |
| Health | http://localhost:3011/api/health |

Stop:

```bash
docker compose down
```

Data lives in the Docker volume `feastpick_feastpick-data` (or project-prefixed). To wipe data: `docker compose down -v`.

### Option B - run the published image (GHCR)

After the first GitHub Release, images are published to GitHub Container Registry:

```text
ghcr.io/letzhub/feastpick:1.0.0
ghcr.io/letzhub/feastpick:1.0
ghcr.io/letzhub/feastpick:latest
```

```bash
# optional: copy and edit
cp .env.example .env
# set FEASTPICK_VERSION=1.0.0 (GHCR_OWNER defaults to fabienonwork)

export GHCR_OWNER=letzhub
export FEASTPICK_VERSION=1.0.0

# pull + run (skip local build)
docker compose pull
docker compose up -d
```

If the package is **private**, authenticate once:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin
```

Public packages can be pulled without login.

### Useful environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FEASTPICK_PORT` | `3011` | Host port mapped to the app |
| `FEASTPICK_VERSION` | `1.0.0` | Image tag / version label |
| `GHCR_OWNER` | `fabienonwork` | GitHub user/org for GHCR image name |
| `FEASTPICK_DATA` | `/app/data` | Data dir **inside** the container |

---

## Run without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
export FEASTPICK_DATA="$(pwd)/data"
uvicorn app.main:app --host 0.0.0.0 --port 3011
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

Interactive docs when the app is running: http://localhost:3011/docs

---

## Versioning & releases

FeastPick follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

| File | Role |
|------|------|
| [`VERSION`](VERSION) | Current version string |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |
| Git tag `vX.Y.Z` | Triggers image build + GitHub Release |

**Maintainer release checklist** is in [`CONTRIBUTING.md`](CONTRIBUTING.md).

Example:

```bash
# after updating VERSION + CHANGELOG
git add VERSION CHANGELOG.md
git commit -m "chore(release): v1.0.0"
git tag -a v1.0.0 -m "v1.0.0"
git push origin main --tags
```

---

## GitHub Container Registry

The [release workflow](.github/workflows/release.yml) runs on tags matching `v*`:

1. Builds the Docker image (linux/amd64)
2. Pushes to `ghcr.io/<github-owner>/feastpick`
3. Creates a GitHub Release with notes

Image tags published per release `v1.2.3`:

- `1.2.3` (exact)
- `1.2` (minor line)
- `1` (major line)
- `latest` (newest stable tag build)

**First-time GHCR visibility:** after the first successful release, open  
**GitHub → Packages → feastpick → Package settings → Change visibility → Public**  
if you want anonymous pulls.

CI (pull requests / `main`) only builds the image; it does not push.

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
4. Pin the image tag (`1.0.0`) instead of `latest`

---

## License

[MIT](LICENSE) © FeastPick contributors
