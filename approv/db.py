from __future__ import annotations

import sqlite3
import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path

import yaml
import bcrypt

logger = logging.getLogger(__name__)

_write_lock = threading.Lock()


class DatabaseManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get("APPROV_DB_PATH", "approv.db")

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def execute_write(self, sql: str, params: tuple = ()) -> int:
        """Thread-safe write operation. Returns lastrowid."""
        with _write_lock:
            conn = self.get_connection()
            try:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

    def execute_write_many(self, statements: list[tuple[str, tuple]]) -> None:
        """Execute multiple write statements in a single transaction."""
        with _write_lock:
            conn = self.get_connection()
            try:
                for sql, params in statements:
                    conn.execute(sql, params)
                conn.commit()
            finally:
                conn.close()

    def execute_read(self, sql: str, params: tuple = ()) -> list[dict]:
        """Read operation. Returns list of dicts."""
        conn = self.get_connection()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def execute_read_one(self, sql: str, params: tuple = ()) -> dict | None:
        """Read single row. Returns dict or None."""
        conn = self.get_connection()
        try:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # --- Backup / Export / Import ---

    def backup_to_file(self, backup_path: str):
        """Hot backup using sqlite3.backup() API."""
        src = sqlite3.connect(self.db_path)
        dst = sqlite3.connect(backup_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

    def backup_to_s3(self, bucket: str, prefix: str | None = None) -> str:
        """Backup DB to S3 with timestamped key. Returns the S3 key."""
        import boto3

        prefix = prefix or os.environ.get("APPROV_S3_PREFIX", "backups/approv")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = f"/tmp/approv_backup_{timestamp}.db"
        self.backup_to_file(backup_path)
        try:
            s3 = boto3.client("s3")
            key = f"{prefix}/approv_{timestamp}.db"
            s3.upload_file(backup_path, bucket, key)
            return key
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)

    def restore_from_s3(self, bucket: str, key: str):
        """Download a backup from S3 and replace current DB."""
        import boto3

        s3 = boto3.client("s3")
        restore_path = f"{self.db_path}.restore"
        s3.download_file(bucket, key, restore_path)
        os.replace(restore_path, self.db_path)

    def list_s3_backups(self, bucket: str, prefix: str | None = None) -> list[dict]:
        """List available backups in S3."""
        import boto3

        prefix = prefix or os.environ.get("APPROV_S3_PREFIX", "backups/approv")
        s3 = boto3.client("s3")
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        backups = []
        for obj in response.get("Contents", []):
            backups.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })
        return sorted(backups, key=lambda x: x["last_modified"], reverse=True)

    def export_db(self) -> bytes:
        """Return DB file bytes for download."""
        backup_path = f"/tmp/approv_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        self.backup_to_file(backup_path)
        try:
            with open(backup_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)

    def import_db(self, db_bytes: bytes):
        """Replace current DB with uploaded file."""
        import_path = f"{self.db_path}.import"
        with open(import_path, "wb") as f:
            f.write(db_bytes)
        os.replace(import_path, self.db_path)


def init_db(db_manager: DatabaseManager, config_dir: str | None = None):
    """Create all tables and seed initial data."""
    config_dir = config_dir or os.environ.get("APPROV_CONFIG_DIR", "config")

    conn = db_manager.get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT,
                phone TEXT,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL REFERENCES users(user_id),
                role_id INTEGER NOT NULL REFERENCES roles(role_id),
                assigned_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, role_id)
            );

            CREATE TABLE IF NOT EXISTS permissions (
                permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_name TEXT NOT NULL UNIQUE,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER NOT NULL REFERENCES roles(role_id),
                permission_id INTEGER NOT NULL REFERENCES permissions(permission_id),
                PRIMARY KEY (role_id, permission_id)
            );

            CREATE TABLE IF NOT EXISTS workflow_definitions (
                wf_def_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                workflow_yaml TEXT NOT NULL,
                form_yaml TEXT NOT NULL,
                seed_data_json TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS workflow_instances (
                instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                wf_def_id INTEGER NOT NULL REFERENCES workflow_definitions(wf_def_id),
                current_status TEXT NOT NULL DEFAULT 'start',
                form_data TEXT NOT NULL,
                started_by INTEGER NOT NULL REFERENCES users(user_id),
                assigned_role TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_trail (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id INTEGER NOT NULL REFERENCES workflow_instances(instance_id),
                status TEXT NOT NULL,
                action TEXT NOT NULL,
                description TEXT,
                user_id INTEGER REFERENCES users(user_id),
                role_name TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

        # Seed data from users_and_roles.yaml if tables are empty
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            _seed_data(conn, config_dir)

        # Seed workflow definition from config if empty
        wf_count = conn.execute("SELECT COUNT(*) FROM workflow_definitions").fetchone()[0]
        if wf_count == 0:
            _seed_workflow_definition(conn, config_dir)

        conn.commit()
    finally:
        conn.close()


def _seed_data(conn: sqlite3.Connection, config_dir: str):
    """Seed users, roles, and permissions from users_and_roles.yaml."""
    yaml_path = Path(config_dir) / "users_and_roles.yaml"
    if not yaml_path.exists():
        logger.warning(f"Seed file not found: {yaml_path}")
        return

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # Insert roles and collect permissions
    all_permissions = set()
    role_map = {}  # role_name -> role_id
    for role_name, role_data in data.get("Role", {}).items():
        conn.execute(
            "INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)",
            (role_name, f"Seeded role: {role_name}"),
        )
        row = conn.execute("SELECT role_id FROM roles WHERE role_name = ?", (role_name,)).fetchone()
        role_map[role_name] = row[0]

        for perm in role_data.get("Permissions", []):
            all_permissions.add(perm)

    # Insert permissions
    perm_map = {}  # perm_name -> perm_id
    for perm_name in all_permissions:
        conn.execute(
            "INSERT OR IGNORE INTO permissions (permission_name) VALUES (?)",
            (perm_name,),
        )
        row = conn.execute("SELECT permission_id FROM permissions WHERE permission_name = ?", (perm_name,)).fetchone()
        perm_map[perm_name] = row[0]

    # Link roles to permissions
    for role_name, role_data in data.get("Role", {}).items():
        role_id = role_map[role_name]
        for perm_name in role_data.get("Permissions", []):
            perm_id = perm_map[perm_name]
            conn.execute(
                "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                (role_id, perm_id),
            )

    # Insert users
    user_map = {}  # username -> user_id
    for username, user_data in data.get("User", {}).items():
        # Default password is lowercase username
        password_hash = bcrypt.hashpw(username.lower().encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn.execute(
            "INSERT OR IGNORE INTO users (username, email, phone, password_hash) VALUES (?, ?, ?, ?)",
            (username, user_data.get("email", ""), user_data.get("phone", ""), password_hash),
        )
        row = conn.execute("SELECT user_id FROM users WHERE username = ?", (username,)).fetchone()
        user_map[username] = row[0]

    # Link users to roles
    for role_name, role_data in data.get("Role", {}).items():
        role_id = role_map[role_name]
        for username in role_data.get("Users", []):
            if username in user_map:
                conn.execute(
                    "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
                    (user_map[username], role_id),
                )


def _seed_workflow_definition(conn: sqlite3.Connection, config_dir: str):
    """Seed initial workflow definition from config files."""
    config_path = Path(config_dir)
    workflow_path = config_path / "workflow.yaml"
    form_path = config_path / "form.yaml"
    data_path = config_path / "data.json"

    if not workflow_path.exists() or not form_path.exists():
        logger.warning("Workflow or form config not found, skipping seed")
        return

    with open(workflow_path, "r") as f:
        workflow_yaml = f.read()
    with open(form_path, "r") as f:
        form_yaml = f.read()

    seed_data_json = None
    if data_path.exists():
        with open(data_path, "r") as f:
            seed_data_json = f.read()

    # Parse description from workflow YAML
    wf_config = yaml.safe_load(workflow_yaml)
    description = wf_config.get("description", "Default workflow")

    conn.execute(
        "INSERT INTO workflow_definitions (name, description, workflow_yaml, form_yaml, seed_data_json) VALUES (?, ?, ?, ?, ?)",
        ("Default Workflow", description, workflow_yaml, form_yaml, seed_data_json),
    )


# Global singleton
db_manager = DatabaseManager()
