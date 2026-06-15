
import sqlite3
from pathlib import Path
import hashlib, datetime, re

DB_PATH = Path(__file__).parent.parent / "carbonlens.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        persona TEXT,
        city_tier TEXT,
        household_size INTEGER DEFAULT 3,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        logged_at TEXT DEFAULT (datetime('now')),
        transport_em REAL, food_em REAL, electricity_em REAL,
        digital_em REAL, shopping_em REAL, total_em REAL,
        score INTEGER, scenario TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS streaks (
        user_id INTEGER PRIMARY KEY,
        current_streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        last_log_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        badge_name TEXT,
        awarded_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    conn.commit()
    conn.close()


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def validate_password(pw: str):
    """Returns (ok: bool, message: str)"""
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", pw):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", pw):
        return False, "Password must contain at least one number."
    return True, ""


def register_user(username, password, persona, city_tier, household_size):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, persona, city_tier, household_size) VALUES (?,?,?,?,?)",
            (username.strip(), _hash(password), persona, city_tier, household_size),
        )
        conn.commit()
        uid = conn.execute("SELECT id FROM users WHERE username=?", (username.strip(),)).fetchone()["id"]
        conn.execute("INSERT INTO streaks (user_id) VALUES (?)", (uid,))
        conn.commit()
        return True, uid
    except sqlite3.IntegrityError:
        return False, None
    finally:
        conn.close()


def login_user(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username.strip(), _hash(password)),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_log(user_id, breakdown, total, score, scenario):
    conn = get_conn()
    conn.execute(
        """INSERT INTO activity_logs
        (user_id, transport_em, food_em, electricity_em, digital_em, shopping_em, total_em, score, scenario)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (user_id, breakdown["Transport"], breakdown["Food"], breakdown["Electricity"],
         breakdown["Digital"], breakdown["Shopping & Waste"], total, score, scenario),
    )
    conn.commit()
    _update_streak(user_id, conn)
    _check_badges(user_id, conn, total, score)
    conn.close()


def _update_streak(user_id, conn):
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    row = conn.execute("SELECT * FROM streaks WHERE user_id=?", (user_id,)).fetchone()
    if row:
        if row["last_log_date"] == today:
            return
        new_streak = (row["current_streak"] + 1) if row["last_log_date"] == yesterday else 1
        longest = max(row["longest_streak"], new_streak)
        conn.execute(
            "UPDATE streaks SET current_streak=?, longest_streak=?, last_log_date=? WHERE user_id=?",
            (new_streak, longest, today, user_id),
        )
        conn.commit()


def _check_badges(user_id, conn, total, score):
    existing = {r["badge_name"] for r in conn.execute("SELECT badge_name FROM badges WHERE user_id=?", (user_id,)).fetchall()}
    candidates = []
    if total < 120 and "🌱 Green Pioneer" not in existing:
        candidates.append("🌱 Green Pioneer")
    if score >= 80 and "⭐ Carbon Champion" not in existing:
        candidates.append("⭐ Carbon Champion")
    cnt = conn.execute("SELECT COUNT(*) as c FROM activity_logs WHERE user_id=?", (user_id,)).fetchone()["c"]
    if cnt >= 7 and "🔥 7-Day Logger" not in existing:
        candidates.append("🔥 7-Day Logger")
    if cnt >= 30 and "🏆 30-Day Veteran" not in existing:
        candidates.append("🏆 30-Day Veteran")
    s = conn.execute("SELECT current_streak FROM streaks WHERE user_id=?", (user_id,)).fetchone()
    if s and s["current_streak"] >= 3 and "⚡ 3-Day Streak" not in existing:
        candidates.append("⚡ 3-Day Streak")
    for b in candidates:
        conn.execute("INSERT INTO badges (user_id, badge_name) VALUES (?,?)", (user_id, b))
    if candidates:
        conn.commit()


def get_history(user_id, limit=60):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM activity_logs WHERE user_id=? ORDER BY logged_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_streak(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM streaks WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"current_streak": 0, "longest_streak": 0}


def get_badges(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT badge_name, awarded_at FROM badges WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_leaderboard(limit=10):
    conn = get_conn()
    rows = conn.execute("""
        SELECT u.username, u.persona,
               ROUND(AVG(a.total_em), 1) as avg_em,
               ROUND(AVG(a.score), 0)    as avg_score,
               COALESCE(s.current_streak, 0) as streak
        FROM users u
        JOIN activity_logs a ON a.user_id = u.id
        LEFT JOIN streaks s ON s.user_id = u.id
        GROUP BY u.id
        ORDER BY avg_em ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
