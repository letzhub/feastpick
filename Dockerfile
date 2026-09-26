# FeastPick
# Official image: ghcr.io/letzhub/feastpick
# App listens on 8080 inside and outside the container (same port).

FROM python:3.13-alpine AS runtime

ARG VERSION=1.1.0
ARG VCS_REF=local
ARG BUILD_DATE=

LABEL org.opencontainers.image.title="FeastPick" \
      org.opencontainers.image.description="Family feast planner: propose dishes, badge dietary tags, vote, and claim who brings what." \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/letzhub/feastpick" \
      org.opencontainers.image.url="https://github.com/letzhub/feastpick" \
      org.opencontainers.image.vendor="letzhub"

WORKDIR /app

RUN apk add --no-cache curl \
  && addgroup -S -g 1001 app \
  && adduser -S -u 1001 -G app app \
  && mkdir -p /app/data \
  && chown -R app:app /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app VERSION ./VERSION
COPY --chown=app:app app ./app
COPY --chown=app:app static ./static

ENV FEASTPICK_DATA=/app/data
ENV FEASTPICK_VERSION=${VERSION}
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

USER app
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=8s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
