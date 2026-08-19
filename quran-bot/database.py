
import json
import logging
import aiosqlite
from datetime import datetime
from config import DB_PATH, DEFAULT_ADMIN_PERMISSIONS

logger = logging.getLogger(__name__)

class Database:

    _instance: "Database | None" = None

    def __init__(self):
        self.path = DB_PATH

    @classmethod
    def get(cls) -> "Database":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def init(self):
        
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS owners (
                    user_id   INTEGER PRIMARY KEY,
                    username  TEXT,
                    full_name TEXT,
                    added_at  TEXT DEFAULT (datetime('now')),
                    added_by  INTEGER
                );

                CREATE TABLE IF NOT EXISTS bot_admins (
                    user_id     INTEGER PRIMARY KEY,
                    username    TEXT,
                    full_name   TEXT,
                    permissions TEXT DEFAULT '{}',
                    added_at    TEXT DEFAULT (datetime('now')),
                    added_by    INTEGER
                );

                CREATE TABLE IF NOT EXISTS group_settings (
                    chat_id      INTEGER PRIMARY KEY,
                    chat_title   TEXT,
                    chat_type    TEXT,
                    panel_access TEXT DEFAULT 'all_admins',
                    added_at     TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS group_panel_admins (
                    chat_id     INTEGER NOT NULL,
                    user_id     INTEGER NOT NULL,
                    access_type TEXT DEFAULT 'allowed',
                    PRIMARY KEY (chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS schedules (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id        INTEGER NOT NULL,
                    module_key     TEXT NOT NULL,
                    job_data       TEXT NOT NULL,
                    interval_type  TEXT NOT NULL,
                    interval_value INTEGER DEFAULT 1,
                    start_time     TEXT NOT NULL,
                    end_time       TEXT,
                    is_active      INTEGER DEFAULT 1,
                    created_by     INTEGER,
                    created_at     TEXT DEFAULT (datetime('now')),
                    last_run       TEXT,
                    next_run       TEXT
                );
            """)
            await db.commit()
        logger.info("✅ قاعدة البيانات جاهزة")

    async def get_owners(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM owners") as cur:
                return [dict(r) for r in await cur.fetchall()]

    async def get_owner_ids(self) -> list[int]:
        rows = await self.get_owners()
        return [r["user_id"] for r in rows]

    async def is_owner(self, user_id: int) -> bool:
        return user_id in await self.get_owner_ids()

    async def count_owners(self) -> int:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT COUNT(*) FROM owners") as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def add_owner(self, user_id: int, username: str, full_name: str, added_by: int | None = None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO owners (user_id, username, full_name, added_by) VALUES (?,?,?,?)",
                (user_id, username, full_name, added_by)
            )
            await db.commit()

    async def remove_owner(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM owners WHERE user_id=?", (user_id,))
            await db.commit()

    async def get_admins(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM bot_admins") as cur:
                rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["permissions"] = json.loads(d["permissions"] or "{}")
            result.append(d)
        return result

    async def is_bot_admin(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT 1 FROM bot_admins WHERE user_id=?", (user_id,)) as cur:
                return await cur.fetchone() is not None

    async def add_bot_admin(self, user_id: int, username: str, full_name: str,
                            permissions: dict | None = None, added_by: int | None = None):
        perms = json.dumps(permissions or DEFAULT_ADMIN_PERMISSIONS)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO bot_admins (user_id, username, full_name, permissions, added_by) "
                "VALUES (?,?,?,?,?)",
                (user_id, username, full_name, perms, added_by)
            )
            await db.commit()

    async def remove_bot_admin(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM bot_admins WHERE user_id=?", (user_id,))
            await db.commit()

    async def get_admin_permissions(self, user_id: int) -> dict:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT permissions FROM bot_admins WHERE user_id=?", (user_id,)) as cur:
                row = await cur.fetchone()
        if row:
            return json.loads(row[0] or "{}")
        return {}

    async def update_admin_permissions(self, user_id: int, permissions: dict):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE bot_admins SET permissions=? WHERE user_id=?",
                (json.dumps(permissions), user_id)
            )
            await db.commit()

    async def upsert_group(self, chat_id: int, chat_title: str, chat_type: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO group_settings (chat_id, chat_title, chat_type) VALUES (?,?,?)",
                (chat_id, chat_title, chat_type)
            )
            await db.execute(
                "UPDATE group_settings SET chat_title=?, chat_type=? WHERE chat_id=?",
                (chat_title, chat_type, chat_id)
            )
            await db.commit()

    async def get_group(self, chat_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM group_settings WHERE chat_id=?", (chat_id,)) as cur:
                row = await cur.fetchone()
        return dict(row) if row else None

    async def get_panel_access(self, chat_id: int) -> str:
        g = await self.get_group(chat_id)
        return g["panel_access"] if g else "all_admins"

    async def set_panel_access(self, chat_id: int, mode: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE group_settings SET panel_access=? WHERE chat_id=?",
                (mode, chat_id)
            )
            await db.commit()

    async def add_group_panel_admin(self, chat_id: int, user_id: int, access: str = "allowed"):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO group_panel_admins (chat_id, user_id, access_type) VALUES (?,?,?)",
                (chat_id, user_id, access)
            )
            await db.commit()

    async def remove_group_panel_admin(self, chat_id: int, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "DELETE FROM group_panel_admins WHERE chat_id=? AND user_id=?",
                (chat_id, user_id)
            )
            await db.commit()

    async def get_group_panel_admins(self, chat_id: int) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM group_panel_admins WHERE chat_id=?", (chat_id,)
            ) as cur:
                return [dict(r) for r in await cur.fetchall()]

    async def get_group_panel_access_type(self, chat_id: int, user_id: int) -> str | None:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT access_type FROM group_panel_admins WHERE chat_id=? AND user_id=?",
                (chat_id, user_id)
            ) as cur:
                row = await cur.fetchone()
        return row[0] if row else None

    async def add_schedule(self, chat_id: int, module_key: str, job_data: dict,
                           interval_type: str, interval_value: int,
                           start_time: str, end_time: str | None,
                           created_by: int) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """INSERT INTO schedules
                   (chat_id, module_key, job_data, interval_type, interval_value,
                    start_time, end_time, created_by, next_run)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (chat_id, module_key, json.dumps(job_data), interval_type,
                 interval_value, start_time, end_time, created_by, start_time)
            )
            await db.commit()
            return cur.lastrowid  

    async def get_active_schedules(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM schedules WHERE is_active=1"
            ) as cur:
                rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["job_data"] = json.loads(d["job_data"])
            result.append(d)
        return result

    async def get_schedules_for_chat(self, chat_id: int) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM schedules WHERE chat_id=? AND is_active=1 ORDER BY id DESC",
                (chat_id,)
            ) as cur:
                rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["job_data"] = json.loads(d["job_data"])
            result.append(d)
        return result

    async def deactivate_schedule(self, schedule_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE schedules SET is_active=0 WHERE id=?", (schedule_id,)
            )
            await db.commit()

    async def update_schedule_last_run(self, schedule_id: int, next_run: str):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE schedules SET last_run=?, next_run=? WHERE id=?",
                (now, next_run, schedule_id)
            )
            await db.commit()
