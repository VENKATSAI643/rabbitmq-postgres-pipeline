"""
db/setup.py
-----------
Run this ONCE to create the database, user, and events table in PostgreSQL.

Usage (inside WSL, from project root):
    python db/setup.py
"""

import sys
import os

# Allow importing config.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ── Step 1: connect as the postgres superuser ─────────────────────────────────
# Uses Unix socket (no host) so peer/trust auth works without a password.
# If this fails, run first in WSL:
#   sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
# then change ADMIN_CONN to: dict(host="localhost", port=5432, user="postgres", password="postgres", dbname="postgres")
ADMIN_CONN = dict(user="postgres", dbname="postgres")   # unix socket — no password

def create_db_and_user():
    try:
        conn = psycopg2.connect(**ADMIN_CONN)
    except psycopg2.OperationalError:
        # Fallback to TCP with password
        conn = psycopg2.connect(
            host="localhost", port=5432,
            user="postgres", password="postgres", dbname="postgres"
        )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pipeline_user') THEN
                CREATE USER pipeline_user WITH PASSWORD 'secret';
            END IF;
        END
        $$;
    """)
    print("[✔] User 'pipeline_user' ready.")

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'pipeline_db'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE pipeline_db OWNER pipeline_user")
        print("[✔] Database 'pipeline_db' created.")
    else:
        print("[i] Database 'pipeline_db' already exists — skipping.")

    cur.execute("GRANT ALL PRIVILEGES ON DATABASE pipeline_db TO pipeline_user")
    cur.close()
    conn.close()

# ── Step 2: create the events table ──────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id          SERIAL       PRIMARY KEY,
    routing_key VARCHAR(100) NOT NULL,
    payload     JSONB        NOT NULL,
    received_at TIMESTAMPTZ  DEFAULT NOW()
);
"""

def create_table():
    import config
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()
    print("[✔] Table 'events' ready.")

if __name__ == "__main__":
    print("=== DB Setup ===")
    create_db_and_user()
    create_table()
    print("=== Setup complete! ===")

