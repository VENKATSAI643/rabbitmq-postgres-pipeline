"""
consumer/consumer.py
--------------------
Subscribes to a RabbitMQ Topic Exchange queue and persists every
received message into the PostgreSQL `events` table.

Binding patterns (from config.py):
  - order.*   →  matches order.created, order.shipped, order.canceled …
  - user.#    →  matches user.signup, user.login, user.profile.updated …

Usage (inside WSL, from project root — keep this running in a dedicated terminal):
    python consumer/consumer.py
"""

import sys
import os

# Allow importing config.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import signal
import psycopg2
import psycopg2.pool
import pika
import config

# ── PostgreSQL connection pool ────────────────────────────────────────────────
db_pool: psycopg2.pool.SimpleConnectionPool | None = None

def init_db_pool():
    global db_pool
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    print("[✔] PostgreSQL connection pool created.")

# ── Persist one event to the database ────────────────────────────────────────
INSERT_SQL = "INSERT INTO events (routing_key, payload) VALUES (%s, %s)"

def save_event(routing_key: str, payload: dict) -> int:
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute(INSERT_SQL, (routing_key, json.dumps(payload)))
        conn.commit()
        cur.execute("SELECT lastval()")
        row_id = cur.fetchone()[0]
        cur.close()
        return row_id
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)

# ── RabbitMQ callback ─────────────────────────────────────────────────────────
def on_message(channel, method, properties, body):
    routing_key = method.routing_key
    try:
        payload = json.loads(body)
        row_id  = save_event(routing_key, payload)
        print(f"  [✔] Saved  [{routing_key:20s}]  → events.id={row_id}  |  {payload}")
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError as exc:
        print(f"  [✘] JSON parse error on [{routing_key}]: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as exc:
        print(f"  [✘] DB error on [{routing_key}]: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# ── Build RabbitMQ channel ────────────────────────────────────────────────────
def build_channel():
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters  = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    connection = pika.BlockingConnection(parameters)
    channel    = connection.channel()

    channel.exchange_declare(
        exchange=config.EXCHANGE_NAME,
        exchange_type=config.EXCHANGE_TYPE,
        durable=True,
    )
    channel.queue_declare(queue=config.QUEUE_NAME, durable=True)

    for key in config.BINDING_KEYS:
        channel.queue_bind(
            exchange=config.EXCHANGE_NAME,
            queue=config.QUEUE_NAME,
            routing_key=key,
        )
        print(f"  [~] Bound pattern '{key}' → queue '{config.QUEUE_NAME}'")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=config.QUEUE_NAME, on_message_callback=on_message)
    return connection, channel

# ── Graceful shutdown ─────────────────────────────────────────────────────────
def handle_shutdown(sig, frame):
    print("\n[!] Shutdown signal received — stopping consumer …")
    sys.exit(0)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    signal.signal(signal.SIGINT,  handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    print("=== Consumer started ===")
    print(f"    Exchange      : {config.EXCHANGE_NAME} ({config.EXCHANGE_TYPE})")
    print(f"    Queue         : {config.QUEUE_NAME}")
    print(f"    Binding keys  : {config.BINDING_KEYS}")
    print(f"    Broker        : {config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}")
    print(f"    Database      : {config.DB_NAME} @ {config.DB_HOST}\n")

    init_db_pool()
    connection, channel = build_channel()

    print("\n[*] Waiting for messages … (CTRL+C to stop)\n")
    channel.start_consuming()

if __name__ == "__main__":
    main()

