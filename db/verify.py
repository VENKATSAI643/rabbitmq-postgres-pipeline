"""
db/verify.py
------------
Quick sanity check — prints all rows from the events table.

Usage (inside WSL, from project root):
    python db/verify.py
"""

import sys
import os

# Allow importing config.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import psycopg2
import config

def main():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    cur = conn.cursor()
    cur.execute("SELECT id, routing_key, payload, received_at FROM events ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No events found in the database yet.")
        return

    print(f"\n{'ID':<5} {'ROUTING KEY':<22} {'RECEIVED AT':<35} PAYLOAD")
    print("─" * 110)
    for row_id, rkey, payload, ts in rows:
        print(f"{row_id:<5} {rkey:<22} {str(ts):<35} {json.dumps(payload)}")

    print(f"\n  Total: {len(rows)} event(s)\n")

if __name__ == "__main__":
    main()

