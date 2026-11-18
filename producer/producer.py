"""
producer/producer.py
--------------------
Publishes sample messages to a RabbitMQ Topic Exchange.

Each message carries:
  - a routing key  (e.g. "order.created", "user.signup")
  - a JSON payload

Usage (inside WSL, from project root):
    python producer/producer.py
"""

import sys
import os

# Allow importing config.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import pika
import config

# ── Sample messages to publish ────────────────────────────────────────────────
SAMPLE_MESSAGES = [
    ("order.created",   {"order_id": 101, "user_id": 1,  "amount": 299.99, "currency": "USD"}),
    ("order.shipped",   {"order_id": 101, "carrier": "DHL",  "tracking": "1Z999AA10123456784"}),
    ("user.signup",     {"user_id": 2,    "email": "alice@example.com", "plan": "free"}),
    ("user.login",      {"user_id": 2,    "ip": "192.168.1.10"}),
    ("order.canceled",  {"order_id": 102, "reason": "out of stock"}),
    ("order.created",   {"order_id": 103, "user_id": 3,  "amount": 49.00,  "currency": "EUR"}),
    ("payment.success", {"order_id": 103, "gateway": "stripe", "txn_id": "ch_abc123"}),
]

# ── Connection helper ─────────────────────────────────────────────────────────
def get_channel():
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters  = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
    )
    connection = pika.BlockingConnection(parameters)
    channel    = connection.channel()
    channel.exchange_declare(
        exchange=config.EXCHANGE_NAME,
        exchange_type=config.EXCHANGE_TYPE,
        durable=True,
    )
    return connection, channel

# ── Publish a single message ──────────────────────────────────────────────────
def publish(channel, routing_key: str, data: dict):
    channel.basic_publish(
        exchange=config.EXCHANGE_NAME,
        routing_key=routing_key,
        body=json.dumps(data),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,          # persistent — survives broker restart
        ),
    )
    print(f"  [→] Published  [{routing_key:20s}]  {data}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"=== Producer started ===")
    print(f"    Exchange : {config.EXCHANGE_NAME} ({config.EXCHANGE_TYPE})")
    print(f"    Broker   : {config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}\n")

    connection, channel = get_channel()
    try:
        for routing_key, payload in SAMPLE_MESSAGES:
            publish(channel, routing_key, payload)
            time.sleep(0.5)
    finally:
        connection.close()

    print("\n=== All messages published. Connection closed. ===")

if __name__ == "__main__":
    main()

