"""SQLite helpers for FeastPick."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DATA_DIR = Path(os.environ.get("FEASTPICK_DATA", "/app/data"))
DB_PATH = DATA_DIR / "feastpick.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


ALLOWED_TAGS = ("vegan", "alcoholic", "fish", "meat")
TAG_META = {
    "vegan": {"label": "Vegan", "icon": "🌱"},
    "alcoholic": {"label": "Alcohol", "icon": "🍷"},
    "fish": {"label": "Fish", "icon": "🐟"},
    "meat": {"label": "Meat", "icon": "🥩"},
}

CATEGORY_ICONS = (
    "🍽️", "🥂", "🍷", "🍺", "☕", "🥤",
    "🥗", "🍲", "🥘", "🍖", "🦃", "🍝",
    "🍰", "🥧", "🍮", "🧀", "🥖", "🍿",
    "🎄", "✨", "🔥", "❄️", "🎁", "⭐",
)


def _normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw.strip().startswith("[") else [t.strip() for t in raw.split(",") if t.strip()]
        except json.JSONDecodeError:
            raw = [t.strip() for t in raw.split(",") if t.strip()]
    if not isinstance(raw, (list, tuple)):
        return []
    out: list[str] = []
    for t in raw:
        key = str(t).strip().lower()
        if key in ALLOWED_TAGS and key not in out:
            out.append(key)
    return out


def tags_to_json(tags: list[str] | None) -> str:
    return json.dumps(_normalize_tags(tags or []))


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY,
              slug TEXT UNIQUE NOT NULL,
              title TEXT NOT NULL,
              event_date TEXT NOT NULL,
              max_votes INTEGER NOT NULL DEFAULT 2,
              created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS categories (
              id TEXT PRIMARY KEY,
              event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
              name TEXT NOT NULL,
              description TEXT NOT NULL DEFAULT '',
              sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS options (
              id TEXT PRIMARY KEY,
              category_id TEXT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
              name TEXT NOT NULL,
              added_by TEXT NOT NULL,
              brought_by TEXT,
              created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS votes (
              option_id TEXT NOT NULL REFERENCES options(id) ON DELETE CASCADE,
              voter TEXT NOT NULL,
              PRIMARY KEY (option_id, voter)
            );

            CREATE INDEX IF NOT EXISTS idx_cat_event ON categories(event_id);
            CREATE INDEX IF NOT EXISTS idx_opt_cat ON options(category_id);
            CREATE INDEX IF NOT EXISTS idx_votes_opt ON votes(option_id);
            """
        )
        _ensure_column(conn, "categories", "icon", "TEXT NOT NULL DEFAULT '🍽️'")
        _ensure_column(conn, "options", "tags", "TEXT NOT NULL DEFAULT '[]'")


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def slugify(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return (s[:40] or "feast") + "-" + new_id()[:6]


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def event_bundle(conn: sqlite3.Connection, event_id: str) -> dict[str, Any] | None:
    ev = conn.execute("SELECT * FROM events WHERE id = ? OR slug = ?", (event_id, event_id)).fetchone()
    if not ev:
        return None
    eid = ev["id"]
    cats = conn.execute(
        "SELECT * FROM categories WHERE event_id = ? ORDER BY sort_order, name",
        (eid,),
    ).fetchall()
    out_cats = []
    for c in cats:
        opts = conn.execute(
            "SELECT * FROM options WHERE category_id = ? ORDER BY created_at",
            (c["id"],),
        ).fetchall()
        options = []
        for o in opts:
            voters = [
                r["voter"]
                for r in conn.execute(
                    "SELECT voter FROM votes WHERE option_id = ? ORDER BY voter COLLATE NOCASE",
                    (o["id"],),
                ).fetchall()
            ]
            tags = _normalize_tags(o["tags"] if "tags" in o.keys() else "[]")
            options.append(
                {
                    "id": o["id"],
                    "name": o["name"],
                    "added_by": o["added_by"],
                    "brought_by": o["brought_by"],
                    "tags": tags,
                    "voters": voters,
                    "vote_count": len(voters),
                }
            )
        # sort options by votes desc then name
        options.sort(key=lambda x: (-x["vote_count"], x["name"].lower()))
        icon = (c["icon"] if "icon" in c.keys() else None) or "🍽️"
        out_cats.append(
            {
                "id": c["id"],
                "name": c["name"],
                "description": c["description"] or "",
                "icon": icon,
                "sort_order": c["sort_order"],
                "options": options,
            }
        )
    return {
        "id": ev["id"],
        "slug": ev["slug"],
        "title": ev["title"],
        "event_date": ev["event_date"],
        "max_votes": ev["max_votes"],
        "created_at": ev["created_at"],
        "categories": out_cats,
    }


def seed_demo() -> str:
    """Create Christmas demo if missing. Returns slug."""
    with db() as conn:
        existing = conn.execute(
            "SELECT id, slug FROM events WHERE slug LIKE 'christmas-eve%' LIMIT 1"
        ).fetchone()
        if existing:
            # backfill icons/tags on demo if empty
            _backfill_demo_icons_tags(conn, existing["id"])
            return existing["slug"]

        eid = new_id()
        slug = "christmas-eve-demo"
        now = time.time()
        conn.execute(
            "INSERT INTO events (id, slug, title, event_date, max_votes, created_at) VALUES (?,?,?,?,?,?)",
            (eid, slug, "Christmas Eve Family Meal", "2026-12-24", 2, now),
        )
        # (name, desc, icon, [(option, author, tags), ...])
        demo_cats = [
            (
                "Drinks",
                "What should be on the table to drink? Pick your favourites  -  max 2 votes.",
                "🥂",
                [
                    ("Champagne", "Alice", ["alcoholic"]),
                    ("Mulled wine", "Bob", ["alcoholic"]),
                    ("Soft drinks", "Carol", ["vegan"]),
                    ("Beer selection", "Dave", ["alcoholic"]),
                ],
            ),
            (
                "Main dishes",
                "Hearty centrepieces. Vote for what you most want to see.",
                "🍽️",
                [
                    ("Roast turkey", "Alice", ["meat"]),
                    ("Vegan lasagna", "Bob", ["vegan"]),
                    ("Beef wellington", "Carol", ["meat"]),
                    ("Baked salmon", "Pascal", ["fish"]),
                ],
            ),
            (
                "Desserts",
                "Sweet finish. Describe any dietary notes when you add an option.",
                "🍰",
                [
                    ("Yule log", "Dave", []),
                    ("Apple pie", "Alice", ["vegan"]),
                    ("Chocolate mousse", "Fabien", []),
                ],
            ),
            (
                "Sides & extras",
                "Salads, breads, cheeses  -  the supporting cast.",
                "🥗",
                [
                    ("Roasted root vegetables", "Bob", ["vegan"]),
                    ("Cheese board", "Carol", []),
                ],
            ),
        ]
        for i, (name, desc, icon, options) in enumerate(demo_cats):
            cid = new_id()
            conn.execute(
                "INSERT INTO categories (id, event_id, name, description, icon, sort_order) VALUES (?,?,?,?,?,?)",
                (cid, eid, name, desc, icon, i),
            )
            for oname, author, tags in options:
                oid = new_id()
                conn.execute(
                    "INSERT INTO options (id, category_id, name, added_by, brought_by, created_at, tags) VALUES (?,?,?,?,?,?,?)",
                    (oid, cid, oname, author, None, now, tags_to_json(tags)),
                )
        # sample votes
        champagne = conn.execute(
            "SELECT o.id FROM options o JOIN categories c ON o.category_id=c.id WHERE c.event_id=? AND o.name=?",
            (eid, "Champagne"),
        ).fetchone()
        mulled = conn.execute(
            "SELECT o.id FROM options o JOIN categories c ON o.category_id=c.id WHERE c.event_id=? AND o.name=?",
            (eid, "Mulled wine"),
        ).fetchone()
        if champagne and mulled:
            for v in ("Alice", "Bob", "Pascal", "Fabien"):
                conn.execute(
                    "INSERT OR IGNORE INTO votes (option_id, voter) VALUES (?,?)",
                    (champagne["id"], v),
                )
            for v in ("Alice", "Fabien", "Pascal"):
                conn.execute(
                    "INSERT OR IGNORE INTO votes (option_id, voter) VALUES (?,?)",
                    (mulled["id"], v),
                )
            conn.execute(
                "UPDATE options SET brought_by=? WHERE id=?",
                ("Pascal", champagne["id"]),
            )
        return slug


def _backfill_demo_icons_tags(conn: sqlite3.Connection, event_id: str) -> None:
    """Fill default icons/tags on existing demo rows that lack them."""
    icon_by_name = {
        "drinks": "🥂",
        "main dishes": "🍽️",
        "mains": "🍽️",
        "desserts": "🍰",
        "sides & extras": "🥗",
        "sides": "🥗",
    }
    for cat in conn.execute("SELECT id, name, icon FROM categories WHERE event_id=?", (event_id,)).fetchall():
        icon = (cat["icon"] or "").strip()
        if (not icon) or (icon == "🍽️" and cat["name"].strip().lower() in icon_by_name):
            guessed = icon_by_name.get(cat["name"].strip().lower())
            if guessed:
                conn.execute("UPDATE categories SET icon=? WHERE id=?", (guessed, cat["id"]))
        for opt in conn.execute("SELECT id, name, tags FROM options WHERE category_id=?", (cat["id"],)).fetchall():
            tags = _normalize_tags(opt["tags"] if "tags" in opt.keys() else "[]")
            if tags:
                continue
            n = opt["name"].lower()
            guessed: list[str] = []
            if any(w in n for w in ("vegan", "soft drink", "root vegetable", "salad")):
                guessed.append("vegan")
            if any(w in n for w in ("wine", "beer", "champagne", "alcohol", "mulled")):
                guessed.append("alcoholic")
            if any(w in n for w in ("salmon", "fish", "cod", "tuna", "shrimp")):
                guessed.append("fish")
            if any(w in n for w in ("turkey", "beef", "meat", "chicken", "lamb", "pork", "wellington")):
                guessed.append("meat")
            if guessed:
                conn.execute("UPDATE options SET tags=? WHERE id=?", (tags_to_json(guessed), opt["id"]))
