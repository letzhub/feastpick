"""FeastPick API — family feast planning with voting."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import (
    CATEGORY_ICONS,
    TAG_META,
    db,
    event_bundle,
    init_db,
    new_id,
    seed_demo,
    slugify,
    tags_to_json,
    _normalize_tags,
)

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"


def _read_version() -> str:
    import os

    env = (os.environ.get("FEASTPICK_VERSION") or "").strip()
    if env:
        return env
    vf = ROOT / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip() or "0.0.0"
    return "0.0.0"


APP_VERSION = _read_version()
app = FastAPI(title="FeastPick", version=APP_VERSION)


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_demo()


# ── models ──────────────────────────────────────────────────────────

class CreateEvent(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    event_date: str = Field(min_length=8, max_length=32)
    max_votes: int = Field(default=2, ge=1, le=10)
    categories: list[dict[str, str]] = Field(default_factory=list)
    # categories: [{name, description}]


class PatchEvent(BaseModel):
    title: str | None = None
    event_date: str | None = None
    max_votes: int | None = Field(default=None, ge=1, le=10)


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)
    icon: str = Field(default="🍽️", max_length=8)


class CategoryPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    icon: str | None = Field(default=None, max_length=8)


class OptionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    added_by: str = Field(min_length=1, max_length=60)
    tags: list[str] = Field(default_factory=list)


class OptionPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    tags: list[str] | None = None


def _clean_icon(icon: str | None) -> str:
    i = (icon or "").strip() or "🍽️"
    # keep single emoji-ish token, max 8 chars
    return i[:8]


class VoteIn(BaseModel):
    voter: str = Field(min_length=1, max_length=60)
    vote: bool = True


class BringIn(BaseModel):
    person: str = Field(min_length=1, max_length=60)
    bring: bool = True


# ── health & pages ──────────────────────────────────────────────────

@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "category_icons": list(CATEGORY_ICONS),
        "tags": [
            {"id": k, "label": v["label"], "icon": v["icon"]}
            for k, v in TAG_META.items()
        ],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "feastpick", "version": APP_VERSION}


@app.get("/")
def home_page() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/new")
def new_page() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/e/{slug}")
def event_page(slug: str) -> FileResponse:
    return FileResponse(STATIC / "index.html")


# ── events API ──────────────────────────────────────────────────────

@app.post("/api/events")
def create_event(body: CreateEvent) -> dict[str, Any]:
    title = body.title.strip()
    if not title:
        raise HTTPException(400, "title required")
    eid = new_id()
    slug = slugify(title)
    now = time.time()
    cats = body.categories or [
        {"name": "Drinks", "description": "Beverages for the table", "icon": "🥂"},
        {"name": "Mains", "description": "Main courses", "icon": "🍽️"},
        {"name": "Desserts", "description": "Sweet finishes", "icon": "🍰"},
    ]
    with db() as conn:
        conn.execute(
            "INSERT INTO events (id, slug, title, event_date, max_votes, created_at) VALUES (?,?,?,?,?,?)",
            (eid, slug, title, body.event_date, body.max_votes, now),
        )
        for i, c in enumerate(cats):
            name = (c.get("name") or "").strip()
            if not name:
                continue
            conn.execute(
                "INSERT INTO categories (id, event_id, name, description, icon, sort_order) VALUES (?,?,?,?,?,?)",
                (
                    new_id(),
                    eid,
                    name,
                    (c.get("description") or "").strip(),
                    _clean_icon(c.get("icon")),
                    i,
                ),
            )
        bundle = event_bundle(conn, eid)
    return bundle  # type: ignore


@app.get("/api/events/{event_id}")
def get_event(event_id: str) -> dict[str, Any]:
    with db() as conn:
        bundle = event_bundle(conn, event_id)
    if not bundle:
        raise HTTPException(404, "Event not found")
    return bundle


@app.patch("/api/events/{event_id}")
def patch_event(event_id: str, body: PatchEvent) -> dict[str, Any]:
    with db() as conn:
        ev = conn.execute("SELECT id FROM events WHERE id=? OR slug=?", (event_id, event_id)).fetchone()
        if not ev:
            raise HTTPException(404, "Event not found")
        eid = ev["id"]
        if body.title is not None:
            conn.execute("UPDATE events SET title=? WHERE id=?", (body.title.strip(), eid))
        if body.event_date is not None:
            conn.execute("UPDATE events SET event_date=? WHERE id=?", (body.event_date, eid))
        if body.max_votes is not None:
            conn.execute("UPDATE events SET max_votes=? WHERE id=?", (body.max_votes, eid))
        return event_bundle(conn, eid)  # type: ignore


@app.post("/api/events/{event_id}/categories")
def add_category(event_id: str, body: CategoryIn) -> dict[str, Any]:
    with db() as conn:
        ev = conn.execute("SELECT id FROM events WHERE id=? OR slug=?", (event_id, event_id)).fetchone()
        if not ev:
            raise HTTPException(404, "Event not found")
        eid = ev["id"]
        mx = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) AS m FROM categories WHERE event_id=?",
            (eid,),
        ).fetchone()["m"]
        cid = new_id()
        conn.execute(
            "INSERT INTO categories (id, event_id, name, description, icon, sort_order) VALUES (?,?,?,?,?,?)",
            (cid, eid, body.name.strip(), body.description.strip(), _clean_icon(body.icon), mx + 1),
        )
        return event_bundle(conn, eid)  # type: ignore


@app.patch("/api/categories/{category_id}")
def patch_category(category_id: str, body: CategoryPatch) -> dict[str, Any]:
    with db() as conn:
        cat = conn.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()
        if not cat:
            raise HTTPException(404, "Category not found")
        if body.name is not None:
            conn.execute("UPDATE categories SET name=? WHERE id=?", (body.name.strip(), category_id))
        if body.description is not None:
            conn.execute(
                "UPDATE categories SET description=? WHERE id=?",
                (body.description.strip(), category_id),
            )
        if body.icon is not None:
            conn.execute(
                "UPDATE categories SET icon=? WHERE id=?",
                (_clean_icon(body.icon), category_id),
            )
        return event_bundle(conn, cat["event_id"])  # type: ignore


@app.delete("/api/categories/{category_id}")
def delete_category(category_id: str) -> dict[str, Any]:
    with db() as conn:
        cat = conn.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()
        if not cat:
            raise HTTPException(404, "Category not found")
        eid = cat["event_id"]
        conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        return event_bundle(conn, eid)  # type: ignore


@app.post("/api/categories/{category_id}/options")
def add_option(category_id: str, body: OptionIn) -> dict[str, Any]:
    with db() as conn:
        cat = conn.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()
        if not cat:
            raise HTTPException(404, "Category not found")
        oid = new_id()
        conn.execute(
            "INSERT INTO options (id, category_id, name, added_by, brought_by, created_at, tags) VALUES (?,?,?,?,?,?,?)",
            (
                oid,
                category_id,
                body.name.strip(),
                body.added_by.strip(),
                None,
                time.time(),
                tags_to_json(body.tags),
            ),
        )
        return event_bundle(conn, cat["event_id"])  # type: ignore


@app.patch("/api/options/{option_id}")
def patch_option(option_id: str, body: OptionPatch) -> dict[str, Any]:
    with db() as conn:
        opt = conn.execute(
            "SELECT o.*, c.event_id FROM options o JOIN categories c ON o.category_id=c.id WHERE o.id=?",
            (option_id,),
        ).fetchone()
        if not opt:
            raise HTTPException(404, "Option not found")
        if body.name is not None:
            conn.execute("UPDATE options SET name=? WHERE id=?", (body.name.strip(), option_id))
        if body.tags is not None:
            conn.execute("UPDATE options SET tags=? WHERE id=?", (tags_to_json(body.tags), option_id))
        return event_bundle(conn, opt["event_id"])  # type: ignore


@app.delete("/api/options/{option_id}")
def delete_option(option_id: str) -> dict[str, Any]:
    with db() as conn:
        opt = conn.execute(
            "SELECT o.*, c.event_id FROM options o JOIN categories c ON o.category_id=c.id WHERE o.id=?",
            (option_id,),
        ).fetchone()
        if not opt:
            raise HTTPException(404, "Option not found")
        eid = opt["event_id"]
        conn.execute("DELETE FROM options WHERE id=?", (option_id,))
        return event_bundle(conn, eid)  # type: ignore


@app.post("/api/options/{option_id}/vote")
def vote_option(option_id: str, body: VoteIn) -> dict[str, Any]:
    voter = body.voter.strip()
    if not voter:
        raise HTTPException(400, "voter required")
    with db() as conn:
        opt = conn.execute(
            "SELECT o.*, c.event_id, c.id AS cat_id FROM options o JOIN categories c ON o.category_id=c.id WHERE o.id=?",
            (option_id,),
        ).fetchone()
        if not opt:
            raise HTTPException(404, "Option not found")
        eid = opt["event_id"]
        cat_id = opt["cat_id"]
        ev = conn.execute("SELECT max_votes FROM events WHERE id=?", (eid,)).fetchone()
        max_votes = ev["max_votes"] if ev else 2

        existing = conn.execute(
            "SELECT 1 FROM votes WHERE option_id=? AND voter=? COLLATE NOCASE",
            (option_id, voter),
        ).fetchone()

        if body.vote:
            if existing:
                return event_bundle(conn, eid)  # type: ignore
            # count votes by this person in this category
            used = conn.execute(
                """
                SELECT COUNT(*) AS n FROM votes v
                JOIN options o ON v.option_id = o.id
                WHERE o.category_id = ? AND v.voter = ? COLLATE NOCASE
                """,
                (cat_id, voter),
            ).fetchone()["n"]
            if used >= max_votes:
                raise HTTPException(
                    409,
                    detail=f"You already used your {max_votes} vote(s) in this category",
                )
            conn.execute("INSERT INTO votes (option_id, voter) VALUES (?,?)", (option_id, voter))
        else:
            conn.execute(
                "DELETE FROM votes WHERE option_id=? AND voter=? COLLATE NOCASE",
                (option_id, voter),
            )
        return event_bundle(conn, eid)  # type: ignore


@app.post("/api/options/{option_id}/bring")
def bring_option(option_id: str, body: BringIn) -> dict[str, Any]:
    person = body.person.strip()
    with db() as conn:
        opt = conn.execute(
            "SELECT o.*, c.event_id FROM options o JOIN categories c ON o.category_id=c.id WHERE o.id=?",
            (option_id,),
        ).fetchone()
        if not opt:
            raise HTTPException(404, "Option not found")
        if body.bring:
            if opt["brought_by"] and opt["brought_by"].lower() != person.lower():
                raise HTTPException(409, detail=f"Already brought by {opt['brought_by']}")
            conn.execute("UPDATE options SET brought_by=? WHERE id=?", (person, option_id))
        else:
            # only the bringer can unbring
            if opt["brought_by"] and opt["brought_by"].lower() != person.lower():
                raise HTTPException(403, detail="Only the bringer can release this")
            conn.execute("UPDATE options SET brought_by=NULL WHERE id=?", (option_id,))
        return event_bundle(conn, opt["event_id"])  # type: ignore


app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
