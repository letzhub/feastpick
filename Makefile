.PHONY: help build up down logs smoke release-check

help:
	@echo "FeastPick make targets:"
	@echo "  make build   - docker compose build"
	@echo "  make up      - build + start detached"
	@echo "  make down    - stop"
	@echo "  make logs    - follow logs"
	@echo "  make smoke   - health + demo API check"
	@echo "  make release-check - verify VERSION matches latest tag"

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

smoke:
	@curl -fsS http://127.0.0.1:8080/api/health && echo
	@curl -fsS http://127.0.0.1:8080/api/events/christmas-eve-demo >/dev/null && echo "demo ok"

release-check:
	@echo "VERSION=$$(tr -d '[:space:]' < VERSION)"
	@echo "tags: $$(git tag -l 'v*' | tail -5)"
