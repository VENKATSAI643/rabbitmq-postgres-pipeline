"""
Central configuration — edit these values to match your environment.
"""

# ── RabbitMQ ──────────────────────────────────────────────────────────────────
RABBITMQ_HOST     = "localhost"
RABBITMQ_PORT     = 5672
RABBITMQ_USER     = "guest"
RABBITMQ_PASSWORD = "guest"

EXCHANGE_NAME     = "events"          # topic exchange name
EXCHANGE_TYPE     = "topic"
QUEUE_NAME        = "event_queue"
BINDING_KEYS      = ["order.*", "user.#"]   # patterns the consumer binds to

# ── PostgreSQL ────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "pipeline_db"
DB_USER     = "pipeline_user"
DB_PASSWORD = "secret"

