import json
import os
import re
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from markupsafe import Markup, escape
from werkzeug.utils import secure_filename

from drive_sync import DriveAuthRequired, DriveConfigError, DriveSyncManager

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"
UPLOAD_ROOT = BASE_DIR / "uploads"
UPLOAD_DIRS = {
    "image": UPLOAD_ROOT,
    "video": UPLOAD_ROOT,
}
POST_JSON_FILENAME = "post.json"
INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")
LEGACY_UPLOAD_DIRS = {
    "image": BASE_DIR / "static" / "uploads" / "images",
    "video": BASE_DIR / "static" / "uploads" / "videos",
}
ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    "video": {".mp4", ".mov", ".webm", ".mkv"},
}

app = Flask(__name__)
app.secret_key = "local-instagram-content-manager"
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024

TITLE_PATTERN = re.compile(r"^(\d+)_(.*)$")
URL_PATTERN = re.compile(r"https?://[^\s<]+", re.IGNORECASE)
DRIVE_SYNC_JOBS = set()
DRIVE_SYNC_LOCK = threading.Lock()
DRIVE_ACTIVITY = {
    "status": "idle",
    "progress": 0,
    "message": "",
}
DRIVE_ACTIVITY_LOCK = threading.Lock()
POST_JSON_LOCK = threading.Lock()
DRIVE_DELETE_JOB = "__drive_delete__"
DRIVE_RECONCILE_AT = 0


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def post_json_path(post):
    """Return the metadata file path inside the post's existing media folder."""
    relative_media = Path(post["filename"] or "")
    folder = relative_media.parent if str(relative_media.parent) != "." else Path(post["title"])
    path = (UPLOAD_ROOT / folder / POST_JSON_FILENAME).resolve()
    if not path.is_relative_to(UPLOAD_ROOT.resolve()):
        raise ValueError("Invalid post metadata path.")
    return path


def timestamp_in_india(value):
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(INDIA_TIMEZONE).isoformat()


def display_timestamp_in_india(value):
    timestamp = timestamp_in_india(value)
    if not timestamp:
        return ""
    return timestamp.replace("T", " ")


def sqlite_timestamp_for_india_date(value, end_of_day=False):
    local_time = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=INDIA_TIMEZONE)
    if end_of_day:
        local_time += timedelta(days=1) - timedelta(seconds=1)
    return local_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def valid_iso_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def write_post_json(connection, post_id):
    """Atomically write a complete post metadata snapshot beside its media."""
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        return None

    media_rows = connection.execute(
        """
        SELECT id, post_id, filename, media_type, created_at
        FROM post_media
        WHERE post_id = ?
        ORDER BY id
        """,
        (post_id,),
    ).fetchall()
    payload = dict(post)
    payload["is_posted"] = bool(payload["is_posted"])
    payload["created_at"] = timestamp_in_india(payload["created_at"])
    payload["media"] = [
        {**dict(media), "created_at": timestamp_in_india(media["created_at"])}
        for media in media_rows
    ]
    payload["metadata_filename"] = POST_JSON_FILENAME
    payload["timezone"] = "Asia/Kolkata (GMT+05:30)"
    payload["updated_at"] = datetime.now(INDIA_TIMEZONE).isoformat()

    path = post_json_path(post)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{POST_JSON_FILENAME}.tmp")
    with POST_JSON_LOCK:
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    return path


def write_all_posts_json(connection):
    for row in connection.execute("SELECT id FROM posts ORDER BY id").fetchall():
        write_post_json(connection, row["id"])


def init_db():
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            song TEXT,
            filename TEXT NOT NULL,
            media_type TEXT NOT NULL,
            is_posted BOOLEAN DEFAULT 0,
            post_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS post_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            media_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS drive_sync (
            media_id INTEGER PRIMARY KEY,
            post_id INTEGER NOT NULL,
            drive_folder_id TEXT,
            drive_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            progress INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (media_id) REFERENCES post_media (id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS drive_delete_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            title TEXT NOT NULL,
            drive_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS link_previews (
            url TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            title TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS drive_post_json (
            post_id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL DEFAULT 'post.json',
            drive_folder_id TEXT,
            drive_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            progress INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        INSERT INTO post_media (post_id, filename, media_type)
        SELECT posts.id, posts.filename, posts.media_type
        FROM posts
        WHERE NOT EXISTS (
            SELECT 1 FROM post_media WHERE post_media.post_id = posts.id
        )
        """
    )
    migrate_media_storage(db)
    db.execute(
        """
        INSERT OR IGNORE INTO drive_sync (media_id, post_id)
        SELECT post_media.id, post_media.post_id
        FROM post_media
        """
    )
    db.execute(
        """
        INSERT OR IGNORE INTO drive_post_json (post_id)
        SELECT id FROM posts
        """
    )
    db.commit()
    write_all_posts_json(db)
    db.close()


def migrate_media_storage(db):
    """Move legacy static uploads into the single project-level uploads root."""
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

    def safe_relative_path(title, filename):
        folder = secure_filename(title or "")
        basename = secure_filename(Path(filename or "").name)
        if not folder or not basename:
            return None
        return f"{folder}/{basename}"

    def move_record(title, filename, media_type):
        relative_path = safe_relative_path(title, filename)
        if relative_path is None:
            return filename

        destination = (UPLOAD_ROOT / relative_path).resolve()
        if not destination.is_relative_to(UPLOAD_ROOT.resolve()):
            return filename

        source_candidates = []
        current_source = (UPLOAD_ROOT / filename).resolve()
        if current_source.is_relative_to(UPLOAD_ROOT.resolve()):
            source_candidates.append(current_source)

        legacy_root = LEGACY_UPLOAD_DIRS.get(media_type)
        if legacy_root is not None:
            legacy_source = (legacy_root / filename).resolve()
            if legacy_source.is_relative_to(legacy_root.resolve()):
                source_candidates.append(legacy_source)

        source = next((candidate for candidate in source_candidates if candidate.is_file()), None)
        if source is not None and source != destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.move(str(source), str(destination))

        return relative_path if destination.exists() else filename

    posts = db.execute("SELECT id, title, filename, media_type FROM posts").fetchall()
    for post in posts:
        media_rows = db.execute(
            "SELECT id, filename, media_type FROM post_media WHERE post_id = ? ORDER BY id",
            (post["id"],),
        ).fetchall()

        if media_rows:
            first_filename = None
            for media in media_rows:
                updated_filename = move_record(post["title"], media["filename"], media["media_type"])
                if first_filename is None:
                    first_filename = updated_filename
                if updated_filename != media["filename"]:
                    db.execute(
                        "UPDATE post_media SET filename = ? WHERE id = ?",
                        (updated_filename, media["id"]),
                    )
            if first_filename and first_filename != post["filename"]:
                db.execute(
                    "UPDATE posts SET filename = ? WHERE id = ?",
                    (first_filename, post["id"]),
                )
        else:
            updated_filename = move_record(post["title"], post["filename"], post["media_type"])
            if updated_filename != post["filename"]:
                db.execute(
                    "UPDATE posts SET filename = ? WHERE id = ?",
                    (updated_filename, post["id"]),
                )

    # Move any untracked legacy files too, while preserving their relative names.
    for legacy_root in set(LEGACY_UPLOAD_DIRS.values()):
        if not legacy_root.exists():
            continue
        for source in legacy_root.rglob("*"):
            if not source.is_file() or source.name.startswith("."):
                continue
            relative = source.relative_to(legacy_root)
            destination = (UPLOAD_ROOT / relative).resolve()
            if not destination.is_relative_to(UPLOAD_ROOT.resolve()):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.move(str(source), str(destination))


def get_post(post_id):
    return get_db().execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()


def media_path_for(media):
    directory = UPLOAD_DIRS.get(media["media_type"])
    if directory is None:
        return None
    root = directory.resolve()
    path = (root / media["filename"]).resolve()
    if not path.is_relative_to(root):
        return None
    return path


def get_post_media(post):
    rows = get_db().execute(
        """
        SELECT media.id, media.post_id, media.filename, media.media_type,
               COALESCE(drive_sync.status, 'pending') AS drive_status,
               drive_sync.drive_file_id
        FROM post_media AS media
        LEFT JOIN drive_sync ON drive_sync.media_id = media.id
        WHERE media.post_id = ?
        ORDER BY media.id
        """,
        (post["id"],),
    ).fetchall()
    if not rows:
        rows = [{
            "id": None,
            "post_id": post["id"],
            "filename": post["filename"],
            "media_type": post["media_type"],
            "drive_status": "pending",
            "drive_file_id": None,
        }]

    return [
        {**dict(media), "exists": bool(media_path_for(media) and media_path_for(media).exists())}
        for media in rows
    ]


def get_media_item(media_id):
    return get_db().execute(
        """
        SELECT media.id, media.post_id, media.filename, media.media_type, posts.title
        FROM post_media AS media
        JOIN posts ON posts.id = media.post_id
        WHERE media.id = ?
        """,
        (media_id,),
    ).fetchone()


def open_worker_db():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def set_drive_activity(status, progress=0, message=""):
    with DRIVE_ACTIVITY_LOCK:
        DRIVE_ACTIVITY.update({
            "status": status,
            "progress": max(0, min(100, int(progress))),
            "message": message,
        })


def get_drive_activity():
    with DRIVE_ACTIVITY_LOCK:
        return dict(DRIVE_ACTIVITY)


def update_drive_media(connection, media_id, status, progress=0, folder_id=None, file_id=None, error=None):
    cursor = connection.execute(
        """
        UPDATE drive_sync
        SET status = ?, progress = ?, drive_folder_id = COALESCE(?, drive_folder_id),
            drive_file_id = COALESCE(?, drive_file_id), error = ?, updated_at = CURRENT_TIMESTAMP
        WHERE media_id = ?
        """,
        (status, progress, folder_id, file_id, error, media_id),
    )
    connection.commit()
    return cursor.rowcount > 0


def update_drive_json(connection, post_id, status, progress=0, folder_id=None, file_id=None, error=None):
    connection.execute(
        """
        UPDATE drive_post_json
        SET status = ?, progress = ?, drive_folder_id = COALESCE(?, drive_folder_id),
            drive_file_id = COALESCE(?, drive_file_id), error = ?, updated_at = CURRENT_TIMESTAMP
        WHERE post_id = ?
        """,
        (status, progress, folder_id, file_id, error, post_id),
    )
    connection.commit()


def update_drive_post(connection, post_id, status, error=None):
    connection.execute(
        """
        UPDATE drive_sync
        SET status = ?, progress = ?, error = ?, updated_at = CURRENT_TIMESTAMP
        WHERE post_id = ?
        """,
        (status, 0, error, post_id),
    )
    connection.commit()


def reset_drive_media(connection, media_id):
    connection.execute(
        """
        UPDATE drive_sync
        SET status = 'pending', progress = 0, drive_file_id = NULL,
            error = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE media_id = ?
        """,
        (media_id,),
    )
    connection.commit()


def reset_drive_json(connection, post_id):
    connection.execute(
        """
        UPDATE drive_post_json
        SET status = 'pending', progress = 0, error = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE post_id = ?
        """,
        (post_id,),
    )
    connection.commit()


def sync_post_to_drive(post_id):
    connection = open_worker_db()
    try:
        post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        sync_rows = connection.execute(
            """
            SELECT drive_sync.*, post_media.filename, post_media.media_type
            FROM drive_sync
            JOIN post_media ON post_media.id = drive_sync.media_id
            WHERE drive_sync.post_id = ?
            ORDER BY post_media.id
            """,
            (post_id,),
        ).fetchall()
        json_row = connection.execute(
            "SELECT * FROM drive_post_json WHERE post_id = ?",
            (post_id,),
        ).fetchone()
        if post is None or (not sync_rows and json_row is None):
            return

        total = len(sync_rows) + (1 if json_row else 0)
        manager = DriveSyncManager(BASE_DIR)
        try:
            service = manager.authenticate(interactive=False)
            target_folder = manager.get_folder_info(service)
            existing_folder_id = next(
                (
                    row["drive_folder_id"]
                    for row in sync_rows
                    if row["drive_folder_id"]
                ),
                None,
            ) or (json_row["drive_folder_id"] if json_row else None)
            post_folder = (
                {"id": existing_folder_id}
                if existing_folder_id
                else manager.get_or_create_post_folder(
                    service,
                    target_folder["id"],
                    post["title"],
                    target_folder.get("driveId"),
                )
            )
        except DriveAuthRequired as error:
            update_drive_post(connection, post_id, "auth_required", str(error))
            set_drive_activity("auth_required", 0, "Authenticate Google Drive to continue syncing.")
            return
        except Exception as error:
            update_drive_post(connection, post_id, "error", str(error)[:500])
            set_drive_activity("error", 0, "Google Drive sync could not start.")
            return

        had_error = False
        did_upload = False
        for index, row in enumerate(sync_rows):
            if connection.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
                return
            if row["status"] == "synced" and row["drive_file_id"]:
                try:
                    if manager.file_exists(service, row["drive_file_id"]):
                        continue
                    reset_drive_media(connection, row["media_id"])
                except DriveAuthRequired as error:
                    update_drive_post(connection, post_id, "auth_required", str(error))
                    set_drive_activity("auth_required", 0, "Authenticate Google Drive to continue syncing.")
                    return
                except Exception as error:
                    had_error = True
                    update_drive_media(
                        connection,
                        row["media_id"],
                        "error",
                        error=str(error)[:500],
                    )
                    continue

            media = {"filename": row["filename"], "media_type": row["media_type"]}
            local_path = media_path_for(media)
            if local_path is None or not local_path.is_file():
                update_drive_media(
                    connection,
                    row["media_id"],
                    "error",
                    error="Local media file is missing.",
                )
                had_error = True
                continue

            set_drive_activity("syncing", 0, f"Uploading {post['title']} to Google Drive...")
            update_drive_media(
                connection,
                row["media_id"],
                "uploading",
                progress=0,
                folder_id=post_folder["id"],
            )
            try:
                result = manager.upload_file(
                    service,
                    post_folder["id"],
                    local_path,
                    progress_callback=lambda progress, media_id=row["media_id"], file_index=index: (
                        update_drive_media(
                            connection,
                            media_id,
                            "uploading",
                            progress=progress,
                            folder_id=post_folder["id"],
                        ),
                        set_drive_activity(
                            "syncing",
                            ((file_index + (progress / 100)) / total) * 100,
                            f"Uploading {file_index + 1} of {total} media file(s)...",
                        ),
                    ),
                )
                updated = update_drive_media(
                    connection,
                    row["media_id"],
                    "synced",
                    progress=100,
                    folder_id=post_folder["id"],
                    file_id=result.get("id"),
                )
                did_upload = True
                if not updated and result.get("id"):
                    try:
                        manager.delete_file(service, result["id"])
                    except Exception:
                        pass
            except DriveAuthRequired as error:
                update_drive_post(connection, post_id, "auth_required", str(error))
                set_drive_activity("auth_required", 0, "Authenticate Google Drive to continue syncing.")
                return
            except Exception as error:
                had_error = True
                update_drive_media(
                    connection,
                    row["media_id"],
                    "error",
                    folder_id=post_folder["id"],
                    error=str(error)[:500],
                )

        if json_row and json_row["status"] == "synced" and json_row["drive_file_id"]:
            try:
                if manager.file_exists(service, json_row["drive_file_id"]):
                    json_row = None
            except DriveAuthRequired as error:
                update_drive_json(connection, post_id, "auth_required", error=str(error))
                set_drive_activity("auth_required", 0, "Authenticate Google Drive to continue syncing.")
                return
            except Exception:
                pass

        if json_row:
            metadata_path = post_json_path(post)
            if not metadata_path.is_file():
                update_drive_json(
                    connection,
                    post_id,
                    "error",
                    folder_id=post_folder["id"],
                    error="Local post.json file is missing.",
                )
                had_error = True
            else:
                metadata_file_id = json_row["drive_file_id"]
                metadata_exists = False
                if metadata_file_id:
                    try:
                        metadata_exists = manager.file_exists(service, metadata_file_id)
                    except DriveAuthRequired as error:
                        update_drive_json(connection, post_id, "auth_required", error=str(error))
                        set_drive_activity("auth_required", 0, "Authenticate Google Drive to continue syncing.")
                        return
                    except Exception as error:
                        had_error = True
                        update_drive_json(connection, post_id, "error", error=str(error)[:500])

                try:
                    set_drive_activity("syncing", 0, f"Uploading metadata for {post['title']}...")
                    update_drive_json(
                        connection,
                        post_id,
                        "uploading",
                        progress=0,
                        folder_id=post_folder["id"],
                    )
                    progress_callback = lambda progress: (
                        update_drive_json(
                            connection,
                            post_id,
                            "uploading",
                            progress=progress,
                            folder_id=post_folder["id"],
                        ),
                        set_drive_activity(
                            "syncing",
                            ((len(sync_rows) + (progress / 100)) / total) * 100,
                            f"Uploading metadata for {post['title']}...",
                        ),
                    )
                    if metadata_exists:
                        result = manager.update_file(
                            service,
                            metadata_file_id,
                            metadata_path,
                            progress_callback=progress_callback,
                        )
                    else:
                        result = manager.upload_file(
                            service,
                            post_folder["id"],
                            metadata_path,
                            progress_callback=progress_callback,
                        )
                    update_drive_json(
                        connection,
                        post_id,
                        "synced",
                        progress=100,
                        folder_id=post_folder["id"],
                        file_id=result.get("id") or metadata_file_id,
                    )
                    did_upload = True
                except DriveAuthRequired as error:
                    update_drive_json(connection, post_id, "auth_required", error=str(error))
                    set_drive_activity("auth_required", 0, "Authenticate Google Drive to continue syncing.")
                    return
                except Exception as error:
                    update_drive_json(
                        connection,
                        post_id,
                        "error",
                        folder_id=post_folder["id"],
                        error=str(error)[:500],
                    )
                    had_error = True
        if had_error:
            set_drive_activity("error", 0, f"Some media from {post['title']} failed to sync.")
        elif did_upload:
            set_drive_activity("complete", 100, f"{post['title']} synced to Google Drive.")
    finally:
        connection.close()


def start_drive_sync(post_id):
    with DRIVE_SYNC_LOCK:
        if post_id in DRIVE_SYNC_JOBS:
            return
        DRIVE_SYNC_JOBS.add(post_id)

    def worker():
        try:
            sync_post_to_drive(post_id)
        finally:
            with DRIVE_SYNC_LOCK:
                DRIVE_SYNC_JOBS.discard(post_id)

    threading.Thread(target=worker, name=f"drive-sync-{post_id}", daemon=True).start()


def start_pending_drive_syncs():
    connection = open_worker_db()
    try:
        post_ids = connection.execute(
            """
            SELECT DISTINCT post_id FROM drive_sync WHERE status != 'synced'
            UNION
            SELECT post_id FROM drive_post_json WHERE status != 'synced'
            """
        ).fetchall()
    finally:
        connection.close()
    for row in post_ids:
        start_drive_sync(row["post_id"])


def start_drive_reconciliation():
    global DRIVE_RECONCILE_AT
    now = time.monotonic()
    with DRIVE_SYNC_LOCK:
        if now < DRIVE_RECONCILE_AT:
            return
        DRIVE_RECONCILE_AT = now + 30

    connection = open_worker_db()
    try:
        post_ids = connection.execute(
            """
            SELECT DISTINCT post_id FROM drive_sync
            UNION
            SELECT post_id FROM drive_post_json
            """
        ).fetchall()
    finally:
        connection.close()
    for row in post_ids:
        start_drive_sync(row["post_id"])


def sync_pending_drive_deletes():
    connection = open_worker_db()
    try:
        jobs = connection.execute(
            """
            SELECT * FROM drive_delete_jobs
            WHERE status != 'deleted'
            ORDER BY CASE WHEN item_type = 'file' THEN 0 ELSE 1 END, id
            """
        ).fetchall()
        if not jobs:
            return

        set_drive_activity("deleting", 0, "Removing deleted post media from Google Drive...")
        manager = DriveSyncManager(BASE_DIR)
        try:
            service = manager.authenticate(interactive=False)
        except DriveAuthRequired:
            connection.execute(
                "UPDATE drive_delete_jobs SET status = 'auth_required', updated_at = CURRENT_TIMESTAMP"
            )
            connection.commit()
            set_drive_activity("auth_required", 0, "Authenticate Google Drive to finish deletion.")
            return
        except Exception as error:
            connection.execute(
                "UPDATE drive_delete_jobs SET status = 'error', error = ?, updated_at = CURRENT_TIMESTAMP",
                (str(error)[:500],),
            )
            connection.commit()
            set_drive_activity("error", 0, "Google Drive deletion could not start.")
            return

        had_error = False
        total = len(jobs)
        for index, job in enumerate(jobs):
            try:
                manager.delete_file(service, job["drive_id"])
                connection.execute(
                    "UPDATE drive_delete_jobs SET status = 'deleted', error = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (job["id"],),
                )
                connection.commit()
                set_drive_activity(
                    "deleting",
                    ((index + 1) / total) * 100,
                    f"Deleting {index + 1} of {total} Drive item(s)...",
                )
            except Exception as error:
                had_error = True
                connection.execute(
                    "UPDATE drive_delete_jobs SET status = 'error', error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (str(error)[:500], job["id"]),
                )
                connection.commit()

        if had_error:
            set_drive_activity("error", 0, "Some deleted media could not be removed from Google Drive.")
        else:
            connection.execute("DELETE FROM drive_delete_jobs WHERE status = 'deleted'")
            connection.commit()
            set_drive_activity("complete", 100, "Deleted post media removed from Google Drive.")
    finally:
        connection.close()


def start_pending_drive_deletes():
    with DRIVE_SYNC_LOCK:
        if DRIVE_DELETE_JOB in DRIVE_SYNC_JOBS:
            return
        DRIVE_SYNC_JOBS.add(DRIVE_DELETE_JOB)

    def worker():
        try:
            sync_pending_drive_deletes()
        finally:
            with DRIVE_SYNC_LOCK:
                DRIVE_SYNC_JOBS.discard(DRIVE_DELETE_JOB)

    threading.Thread(target=worker, name="drive-delete-sync", daemon=True).start()


# ---------------------------------------------------------------------------
# Title / filename helpers
# ---------------------------------------------------------------------------

def split_title(title):
    """Return (number, text) for a stored title like '3_My_Reel'."""
    match = TITLE_PATTERN.match(title or "")
    if match:
        return int(match.group(1)), match.group(2)
    return None, title or ""


def next_post_number(db):
    """Highest existing numeric prefix + 1 (not row count, so deletes never collide)."""
    numbers = [
        split_title(row["title"])[0]
        for row in db.execute("SELECT title FROM posts")
    ]
    numbers = [n for n in numbers if n is not None]
    return max(numbers) + 1 if numbers else 1


def build_title(number, raw_title):
    """'Ganpati Photo' -> '4_Ganpati_Photo'. Returns (title, error)."""
    slug = secure_filename(raw_title.strip())
    if not slug:
        return None, "Title must contain at least one letter or number."
    return f"{number}_{slug}", None


def valid_url(url):
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_youtube_url(url):
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "youtu.be" or hostname.endswith(".youtube.com") or hostname == "youtube.com"


def youtube_title(url):
    try:
        from yt_dlp import YoutubeDL

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "socket_timeout": 8,
        }
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=False)
        return (info.get("title") or "").strip() or None
    except Exception:
        return None


def cache_youtube_previews(db, values):
    urls = {
        match.group(0).rstrip(".,!?;:)")
        for value in values
        for match in URL_PATTERN.finditer(value or "")
        if is_youtube_url(match.group(0).rstrip(".,!?;:)"))
    }
    for url in urls:
        existing = db.execute("SELECT title FROM link_previews WHERE url = ?", (url,)).fetchone()
        if existing and existing["title"]:
            continue
        db.execute(
            "INSERT OR REPLACE INTO link_previews (url, provider, title, updated_at) VALUES (?, 'youtube', ?, CURRENT_TIMESTAMP)",
            (url, youtube_title(url)),
        )
    db.commit()


def linkify_text(value):
    value = value or ""
    output = []
    last_end = 0
    for match in URL_PATTERN.finditer(value):
        output.append(escape(value[last_end:match.start()]).replace("\n", Markup("<br>")))
        raw_url = match.group(0)
        url = raw_url.rstrip(".,!?;:)")
        trailing = raw_url[len(url):]
        safe_url = escape(url)
        if is_youtube_url(url):
            preview = get_db().execute(
                "SELECT title FROM link_previews WHERE url = ? AND provider = 'youtube'",
                (url,),
            ).fetchone()
            if preview and preview["title"]:
                output.append(Markup(
                    '<span class="youtube-link"><a class="youtube-capsule" href="{}" target="_blank" rel="noopener noreferrer"><span class="youtube-badge" aria-label="YouTube" title="YouTube"><svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg></span><span class="youtube-title">{}</span></a><a class="youtube-fallback" href="{}" target="_blank" rel="noopener noreferrer"><span class="youtube-fallback-url">{}</span><svg class="shrink-0" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg></a></span>'
                ).format(safe_url, escape(preview["title"]), safe_url, safe_url))
            else:
                output.append(Markup('<a class="rich-link" href="{}" target="_blank" rel="noopener noreferrer">{}</a>').format(safe_url, safe_url))
        else:
            output.append(Markup('<a class="rich-link" href="{}" target="_blank" rel="noopener noreferrer">{}</a>').format(safe_url, safe_url))
        output.append(escape(trailing))
        last_end = match.end()
    output.append(escape(value[last_end:]).replace("\n", Markup("<br>")))
    return Markup().join(output)


def media_path(post):
    return media_path_for(post)


def save_upload(file_storage, title, used_filenames=None):
    """Store a file at <media type>/<title>/<filename>."""
    original = secure_filename(file_storage.filename or "")
    ext = Path(original).suffix.lower()

    media_type = None
    for kind, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            media_type = kind
            break
    if media_type is None:
        allowed = ", ".join(sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS["image"] | ALLOWED_EXTENSIONS["video"]))
        return None, None, f"Unsupported file type. Allowed: {allowed}."

    filename = secure_filename(f"{title}{ext}")
    if not filename:
        return None, None, "Could not derive a safe filename from the title."

    used_filenames = used_filenames if used_filenames is not None else set()
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    copy_number = 2
    while filename in used_filenames:
        filename = secure_filename(f"{stem}_{copy_number}{suffix}")
        copy_number += 1

    directory = UPLOAD_DIRS[media_type].resolve()
    relative_filename = f"{title}/{filename}"
    destination = (directory / relative_filename).resolve()
    if not destination.is_relative_to(directory):
        return None, None, "Invalid file path."

    destination.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(destination)
    used_filenames.add(filename)
    return relative_filename, media_type, None


def delete_media_file(post):
    """Remove the physical file; returns an error message or None."""
    path = media_path(post)
    if path is None or not path.exists():
        return None
    try:
        os.remove(path)
    except OSError:
        return "Database record deleted, but the media file could not be removed from disk."

    root = UPLOAD_DIRS[post["media_type"]].resolve()
    if path.parent != root:
        try:
            path.parent.rmdir()
        except OSError:
            pass
    return None


def clean_post_fields(form):
    """Shared validation for add/edit forms. Returns (data, error)."""
    raw_title = (form.get("title") or "").strip()
    if not raw_title:
        return None, "Title cannot be empty."

    is_posted = form.get("is_posted") in ("on", "1", "true")
    post_url = (form.get("post_url") or "").strip()

    if post_url and not valid_url(post_url):
        return None, "Instagram URL is not a valid URL (use http:// or https://)."
    if is_posted and not post_url:
        return None, "An Instagram post URL is required when the post is marked as posted."

    data = {
        "raw_title": raw_title,
        "description": (form.get("description") or "").strip(),
        "song": (form.get("song") or "").strip(),
        "is_posted": 1 if is_posted else 0,
        "post_url": post_url or None,
    }
    return data, None


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

@app.template_filter("post_number")
def post_number_filter(title):
    return split_title(title)[0]


@app.template_filter("title_text")
def title_text_filter(title):
    return split_title(title)[1]


@app.template_filter("file_name")
def file_name_filter(filename):
    return Path(filename or "").name


@app.template_filter("rich_links")
def rich_links_filter(value):
    return linkify_text(value)


@app.template_filter("india_time")
def india_time_filter(value):
    return display_timestamp_in_india(value)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    query = (request.args.get("q") or "").strip()
    sort = request.args.get("sort", "az")
    if sort not in {"az", "za"}:
        sort = "az"
    date_from = (request.args.get("date_from") or "").strip()
    date_to = (request.args.get("date_to") or "").strip()
    not_posted = (request.args.get("not_posted") or "").lower() in {"1", "true", "on"}

    filters = []
    params = []
    if query:
        filters.append("(posts.title LIKE ? COLLATE NOCASE OR posts.description LIKE ? COLLATE NOCASE OR posts.song LIKE ? COLLATE NOCASE)")
        params.extend([f"%{query}%"] * 3)
    if not_posted:
        filters.append("posts.is_posted = 0")
    if valid_iso_date(date_from):
        filters.append("posts.created_at >= ?")
        params.append(sqlite_timestamp_for_india_date(date_from))
    else:
        date_from = ""
    if valid_iso_date(date_to):
        filters.append("posts.created_at <= ?")
        params.append(sqlite_timestamp_for_india_date(date_to, end_of_day=True))
    else:
        date_to = ""

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    posts = get_db().execute(
        f"""
        SELECT posts.*,
               COUNT(DISTINCT post_media.id) AS media_count,
               COUNT(DISTINCT drive_sync.media_id) AS drive_media_count,
               COUNT(DISTINCT CASE WHEN drive_sync.status = 'synced' AND drive_sync.drive_file_id IS NOT NULL THEN drive_sync.media_id END) AS synced_media_count,
               COUNT(DISTINCT CASE WHEN drive_sync.status = 'uploading' THEN drive_sync.media_id END) AS uploading_media_count,
               COUNT(DISTINCT CASE WHEN drive_sync.status IN ('pending', 'auth_required') THEN drive_sync.media_id END) AS pending_media_count,
               COUNT(DISTINCT CASE WHEN drive_sync.status = 'error' THEN drive_sync.media_id END) AS error_media_count
        FROM posts
        LEFT JOIN post_media ON post_media.post_id = posts.id
        LEFT JOIN drive_sync ON drive_sync.media_id = post_media.id
        {where}
        GROUP BY posts.id
        """,
        params,
    ).fetchall()
    posts = sorted(
        posts,
        key=lambda p: (split_title(p["title"])[1].replace("_", " ").casefold(), p["id"]),
        reverse=sort == "za",
    )
    total_posts = get_db().execute("SELECT COUNT(*) AS count FROM posts").fetchone()["count"]
    return render_template(
        "index.html",
        posts=posts,
        total_posts=total_posts,
        query=query,
        sort=sort,
        date_from=date_from,
        date_to=date_to,
        not_posted=not_posted,
        has_filters=bool(query or date_from or date_to or not_posted),
    )


@app.route("/add", methods=["GET", "POST"])
def add_post():
    db = get_db()
    if request.method == "POST":
        data, error = clean_post_fields(request.form)
        media_records = []
        if error is None:
            files = [
                file_storage
                for file_storage in request.files.getlist("media")
                if (file_storage.filename or "").strip()
            ]
            if not files:
                error = "Please choose at least one image or video file to upload."
            else:
                invalid_file = next(
                    (
                        file_storage
                        for file_storage in files
                        if Path(secure_filename(file_storage.filename or "")).suffix.lower()
                        not in ALLOWED_EXTENSIONS["image"] | ALLOWED_EXTENSIONS["video"]
                    ),
                    None,
                )
                if invalid_file is not None:
                    allowed = ", ".join(
                        sorted(
                            extension.lstrip(".")
                            for extension in ALLOWED_EXTENSIONS["image"] | ALLOWED_EXTENSIONS["video"]
                        )
                    )
                    error = f"Unsupported file type in {invalid_file.filename}. Allowed: {allowed}."
                else:
                    title, title_error = build_title(next_post_number(db), data["raw_title"])
                    if title_error:
                        error = title_error
                    else:
                        used_filenames = set()
                        for file_storage in files:
                            filename, media_type, upload_error = save_upload(
                                file_storage,
                                title,
                                used_filenames,
                            )
                            if upload_error:
                                error = upload_error
                                break
                            media_records.append({
                                "filename": filename,
                                "media_type": media_type,
                            })

                    if error is None:
                        cursor = db.execute(
                            """
                            INSERT INTO posts (title, description, song, filename, media_type, is_posted, post_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                title,
                                data["description"],
                                data["song"],
                                media_records[0]["filename"],
                                media_records[0]["media_type"],
                                data["is_posted"],
                                data["post_url"],
                            ),
                        )
                        db.executemany(
                            "INSERT INTO post_media (post_id, filename, media_type) VALUES (?, ?, ?)",
                            [
                                (cursor.lastrowid, media["filename"], media["media_type"])
                                for media in media_records
                            ],
                        )
                        media_rows = db.execute(
                            "SELECT id FROM post_media WHERE post_id = ? ORDER BY id",
                            (cursor.lastrowid,),
                        ).fetchall()
                        db.executemany(
                            "INSERT OR IGNORE INTO drive_sync (media_id, post_id) VALUES (?, ?)",
                            [(media["id"], cursor.lastrowid) for media in media_rows],
                        )
                        db.execute(
                            "INSERT OR IGNORE INTO drive_post_json (post_id) VALUES (?)",
                            (cursor.lastrowid,),
                        )
                        db.commit()
                        cache_youtube_previews(db, [data["description"], data["song"]])
                        write_post_json(db, cursor.lastrowid)
                        start_drive_sync(cursor.lastrowid)
                        flash(
                            f"Post \u201c{title}\u201d created with {len(media_records)} media file(s).",
                            "success",
                        )
                        return redirect(url_for("post_detail", post_id=cursor.lastrowid))

                    for media in media_records:
                        path = media_path_for(media)
                        if path and path.exists():
                            try:
                                path.unlink()
                                path.parent.rmdir()
                            except OSError:
                                pass
                    db.rollback()
        flash(error, "error")

    return render_template("add_post.html", next_number=next_post_number(db))


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)
    return render_template("post_detail.html", post=post, media_files=get_post_media(post))


@app.route("/youtube/metadata")
def youtube_metadata():
    url = (request.args.get("url") or "").strip().rstrip(".,!?;:)")
    if not valid_url(url) or not is_youtube_url(url):
        return jsonify({"error": "Enter a valid YouTube URL."}), 400

    cached = get_db().execute(
        "SELECT title FROM link_previews WHERE url = ? AND provider = 'youtube'",
        (url,),
    ).fetchone()
    if cached and cached["title"]:
        return jsonify({"url": url, "title": cached["title"], "cached": True})

    title = youtube_title(url)
    if not title:
        return jsonify({"error": "The YouTube title could not be fetched."}), 502

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO link_previews (url, provider, title, updated_at) VALUES (?, 'youtube', ?, CURRENT_TIMESTAMP)",
        (url, title),
    )
    db.commit()
    return jsonify({"url": url, "title": title})


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)

    if request.method == "POST":
        data, error = clean_post_fields(request.form)
        if error is None:
            number, _ = split_title(post["title"])
            if number is None:
                number = next_post_number(get_db())
            title, title_error = build_title(number, data["raw_title"])
            if title_error:
                error = title_error
            else:
                db = get_db()
                db.execute(
                    """
                    UPDATE posts
                    SET title = ?, description = ?, song = ?, is_posted = ?, post_url = ?
                    WHERE id = ?
                    """,
                     (title, data["description"], data["song"], data["is_posted"],
                      data["post_url"], post_id),
                )
                db.commit()
                cache_youtube_previews(db, [data["description"], data["song"]])
                write_post_json(db, post_id)
                reset_drive_json(db, post_id)
                flash("Post updated.", "success")
                return redirect(url_for("post_detail", post_id=post_id))
        flash(error, "error")

    _, title_text = split_title(post["title"])
    return render_template("edit_post.html", post=post, title_text=title_text)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    db = get_db()
    post = get_post(post_id)
    if post is None:
        abort(404)
    drive_rows = db.execute(
        "SELECT drive_file_id, drive_folder_id FROM drive_sync WHERE post_id = ?",
        (post_id,),
    ).fetchall()
    json_drive_row = db.execute(
        "SELECT drive_file_id, drive_folder_id FROM drive_post_json WHERE post_id = ?",
        (post_id,),
    ).fetchone()
    drive_file_ids = {row["drive_file_id"] for row in drive_rows if row["drive_file_id"]}
    drive_folder_ids = {row["drive_folder_id"] for row in drive_rows if row["drive_folder_id"]}
    if json_drive_row:
        if json_drive_row["drive_file_id"]:
            drive_file_ids.add(json_drive_row["drive_file_id"])
        if json_drive_row["drive_folder_id"]:
            drive_folder_ids.add(json_drive_row["drive_folder_id"])
    for drive_id in drive_file_ids:
        db.execute(
            "INSERT INTO drive_delete_jobs (post_id, title, drive_id, item_type) VALUES (?, ?, ?, 'file')",
            (post_id, post["title"], drive_id),
        )
    for drive_id in drive_folder_ids:
        db.execute(
            "INSERT INTO drive_delete_jobs (post_id, title, drive_id, item_type) VALUES (?, ?, ?, 'folder')",
            (post_id, post["title"], drive_id),
        )
    metadata_path = post_json_path(post)
    try:
        if metadata_path.exists():
            metadata_path.unlink()
    except OSError:
        pass
    file_errors = [
        error
        for error in (delete_media_file(media) for media in get_post_media(post))
        if error
    ]
    db.execute("DELETE FROM post_media WHERE post_id = ?", (post_id,))
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    if file_errors:
        flash(file_errors[0], "error")
    else:
        flash(f"Post \u201c{post['title']}\u201d deleted.", "success")
    start_pending_drive_deletes()
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>/posted", methods=["POST"])
def mark_posted(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)
    post_url = (request.form.get("post_url") or "").strip()
    if not post_url or not valid_url(post_url):
        flash("Please enter a valid Instagram post URL (http:// or https://).", "error")
        return redirect(url_for("post_detail", post_id=post_id))
    db = get_db()
    db.execute("UPDATE posts SET is_posted = 1, post_url = ? WHERE id = ?", (post_url, post_id))
    db.commit()
    write_post_json(db, post_id)
    flash("Post marked as posted.", "success")
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/drive/status")
def drive_status():
    start_drive_reconciliation()
    pending_delete = get_db().execute(
        """
        SELECT 1
        FROM drive_delete_jobs
        WHERE status = 'pending'
           OR (status = 'error' AND updated_at <= datetime('now', '-15 seconds'))
        LIMIT 1
        """
    ).fetchone()
    if pending_delete:
        start_pending_drive_deletes()
    result = DriveSyncManager(BASE_DIR).status()
    result["activity"] = get_drive_activity()
    return jsonify(result)


@app.route("/drive/login")
def drive_login():
    next_url = request.args.get("next") or url_for("index")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("index")
    post_id = request.args.get("post_id", type=int)
    if post_id and get_post(post_id) is None:
        post_id = None

    try:
        manager = DriveSyncManager(BASE_DIR)
        service = manager.authenticate(interactive=True)
        manager.get_folder_info(service)
        flash("Google Drive connected. Sync will resume automatically.", "success")
        if post_id:
            start_drive_sync(post_id)
        else:
            start_pending_drive_syncs()
        start_pending_drive_deletes()
    except Exception:
        flash("Google Drive login was not completed. Check credentials and folder access.", "error")
    return redirect(next_url)


@app.route("/post/<int:post_id>/sync-status")
def post_sync_status(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)

    rows = get_db().execute(
        "SELECT status, progress, error FROM drive_sync WHERE post_id = ? ORDER BY media_id",
        (post_id,),
    ).fetchall()
    json_row = get_db().execute(
        "SELECT status, progress, error FROM drive_post_json WHERE post_id = ?",
        (post_id,),
    ).fetchone()
    if json_row:
        rows = [*rows, json_row]
    if not rows:
        return jsonify({
            "status": "not_started",
            "progress": 0,
            "total": 0,
            "synced": 0,
            "message": "Drive sync is not queued for this post.",
        })

    statuses = {row["status"] for row in rows}
    progress = round(sum(row["progress"] for row in rows) / len(rows))
    synced = sum(row["status"] == "synced" for row in rows)
    error = next((row["error"] for row in rows if row["error"]), None)

    if "auth_required" in statuses:
        status = "auth_required"
        message = "Google Drive login is required to continue."
    elif "error" in statuses:
        status = "error"
        message = error or "One or more post files failed to sync."
    elif synced == len(rows):
        status = "synced"
        message = f"All {len(rows)} post file(s) synced to Google Drive."
    elif "uploading" in statuses:
        status = "uploading"
        message = f"Uploading {synced} of {len(rows)} post file(s)."
    else:
        status = "pending"
        message = "Waiting for the Google Drive sync worker."

    return jsonify({
        "status": status,
        "progress": progress,
        "total": len(rows),
        "synced": synced,
        "message": message,
    })


@app.route("/media/<int:post_id>")
def serve_media(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)
    media = get_post_media(post)[0]
    path = media_path_for(media)
    if path is None or not path.exists():
        abort(404, description="Media file is missing from disk.")
    return send_from_directory(UPLOAD_DIRS[media["media_type"]], media["filename"])


@app.route("/media/<int:post_id>/download")
def download_media(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)
    media = get_post_media(post)[0]
    path = media_path_for(media)
    if path is None or not path.exists():
        abort(404, description="Media file is missing from disk.")
    ext = Path(media["filename"]).suffix
    return send_from_directory(
        UPLOAD_DIRS[media["media_type"]],
        media["filename"],
        as_attachment=True,
        download_name=f"{post['title']}{ext}",
    )


@app.route("/media/item/<int:media_id>")
def serve_media_item(media_id):
    media = get_media_item(media_id)
    if media is None:
        abort(404)
    path = media_path_for(media)
    if path is None or not path.exists():
        abort(404, description="Media file is missing from disk.")
    return send_from_directory(UPLOAD_DIRS[media["media_type"]], media["filename"])


@app.route("/media/item/<int:media_id>/download")
def download_media_item(media_id):
    media = get_media_item(media_id)
    if media is None:
        abort(404)
    path = media_path_for(media)
    if path is None or not path.exists():
        abort(404, description="Media file is missing from disk.")
    return send_from_directory(
        UPLOAD_DIRS[media["media_type"]],
        media["filename"],
        as_attachment=True,
        download_name=Path(media["filename"]).name,
    )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    description = getattr(e, "description", "Page not found.")
    return render_template("error.html", code=404, message=description), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("error.html", code=405, message="That action is not allowed here."), 405


@app.errorhandler(413)
def too_large(e):
    return render_template("error.html", code=413, message="Uploaded file is too large (max 512 MB)."), 413


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Something went wrong on the server."), 500


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=9999, use_reloader=False)
