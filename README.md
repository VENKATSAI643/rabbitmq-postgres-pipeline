# 🐇 RabbitMQ → PostgreSQL Event Pipeline

A Python-based event streaming pipeline that publishes messages to a **RabbitMQ Topic Exchange** and persists them into a **PostgreSQL** database via a message consumer — running entirely on **WSL (Ubuntu)**.

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How Topic Exchange Works](#how-topic-exchange-works)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Configuration](#configuration)
8. [Running the Pipeline](#running-the-pipeline)
9. [Code Walkthrough](#code-walkthrough)
10. [Database Schema](#database-schema)
11. [Troubleshooting](#troubleshooting)
12. [What's Next](#whats-next)

---

## Overview

This project demonstrates a classic **message-broker pattern**:

- A **Producer** generates events (orders, user actions) and publishes them to RabbitMQ with a **routing key** (e.g. `order.created`, `user.signup`).
- **RabbitMQ** routes each message to the correct queue based on **topic pattern matching**.
- A **Consumer** receives messages from the queue and **inserts them into PostgreSQL**.

This pattern is widely used in microservices, event-driven architectures, and ETL pipelines.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          WSL (Ubuntu)                               │
│                                                                     │
│  ┌─────────────┐    AMQP Publish     ┌──────────────────────────┐  │
│  │             │   routing_key=       │   RabbitMQ Broker        │  │
│  │  producer/  │   order.created  ──▶│   Topic Exchange: events │  │
│  │  producer.py│                     │                          │  │
│  └─────────────┘                     │  Binding patterns:       │  │
│                                      │   order.*  ──┐           │  │
│                                      │   user.#   ──┤           │  │
│                                      │              ▼           │  │
│                                      │   Queue: event_queue     │  │
│                                      └──────────┬───────────────┘  │
│                                                 │ Deliver           │
│                                                 ▼                   │
│                                      ┌──────────────────────────┐  │
│                                      │   consumer/consumer.py   │  │
│                                      │   - Parse JSON           │  │
│                                      │   - INSERT into events   │  │
│                                      └──────────┬───────────────┘  │
│                                                 │                   │
│                                                 ▼                   │
│                                      ┌──────────────────────────┐  │
│                                      │   PostgreSQL             │  │
│                                      │   DB: pipeline_db        │  │
│                                      │   Table: events          │  │
│                                      └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
producer/producer.py
    │
    │  1. Connect to RabbitMQ
    │  2. Declare Topic Exchange ("events")
    │  3. Publish JSON message with routing key
    ▼
RabbitMQ Topic Exchange
    │
    │  4. Match routing key against binding patterns
    │  5. Route to bound queue(s)
    ▼
Queue: event_queue
    │
    │  6. Hold message until consumer picks it up
    ▼
consumer/consumer.py
    │
    │  7. Receive and decode JSON
    │  8. INSERT into PostgreSQL
    │  9. ACK message (removes it from queue)
    ▼
PostgreSQL → events table
```

---

## How Topic Exchange Works

RabbitMQ's **Topic Exchange** routes messages based on routing key patterns using two wildcards:

| Wildcard | Meaning | Example |
|----------|---------|---------|
| `*` | Exactly **one** word | `order.*` matches `order.created` but NOT `order.a.b` |
| `#` | **Zero or more** words | `user.#` matches `user.signup`, `user.profile.updated` |

### Routing in this project

| Message Routing Key | Matches `order.*` | Matches `user.#` | Saved to DB? |
|--------------------|------------------|-----------------|--------------|
| `order.created`    | ✅ Yes            | ❌ No            | ✅ Yes |
| `order.shipped`    | ✅ Yes            | ❌ No            | ✅ Yes |
| `order.canceled`   | ✅ Yes            | ❌ No            | ✅ Yes |
| `user.signup`      | ❌ No             | ✅ Yes           | ✅ Yes |
| `user.login`       | ❌ No             | ✅ Yes           | ✅ Yes |
| `payment.success`  | ❌ No             | ❌ No            | ❌ No (intentionally dropped) |

> **Key insight:** `payment.success` is published but never consumed — no binding pattern matches it. This demonstrates how Topic Exchanges let you selectively consume only the events you care about.

---

## Project Structure

```
e:\Rabitmq\
├── config.py                   # Central config (credentials, exchange, queue names)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── PROGRESS.md                 # Step-by-step setup progress tracker
│
├── producer/
│   ├── __init__.py
│   └── producer.py             # Publishes sample events to RabbitMQ
│
├── consumer/
│   ├── __init__.py
│   └── consumer.py             # Subscribes to queue, writes events to PostgreSQL
│
├── db/
│   ├── __init__.py
│   ├── setup.py                # One-time DB/table creation script
│   └── verify.py               # Utility to print all saved events
│
└── docs/
    └── project_requirement.md  # Original project requirements
```

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| WSL (Ubuntu) | 22.04+ | Windows Subsystem for Linux |
| Python | 3.10+ | Python 3.14 tested |
| RabbitMQ | 3.x+ | With Erlang |
| PostgreSQL | 15+ | v18 tested |

---

## Installation & Setup

> **All commands run inside WSL.** Access the project via `/mnt/e/Rabitmq`.

### 1. Update WSL packages

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install RabbitMQ

```bash
sudo apt install -y erlang
sudo apt install -y rabbitmq-server
sudo service rabbitmq-server start

# Optional: web management UI at http://localhost:15672
sudo rabbitmq-plugins enable rabbitmq_management
```

Verify:
```bash
sudo rabbitmqctl status
```

### 3. Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start
```

### 4. Set up Python environment

```bash
cd /mnt/e/Rabitmq

# Install build dependencies (required for Python 3.14+)
sudo apt install -y libpq-dev python3-dev

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 5. Create the database

```bash
# If postgres user has no password yet:
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# Run the DB setup script
python db/setup.py
```

Expected output:
```
=== DB Setup ===
[✔] User 'pipeline_user' ready.
[✔] Database 'pipeline_db' created.
[✔] Table 'events' ready.
=== Setup complete! ===
```

---

## Configuration

All settings live in [`config.py`](config.py) at the project root.

```python
# RabbitMQ
RABBITMQ_HOST     = "localhost"
RABBITMQ_PORT     = 5672
RABBITMQ_USER     = "guest"
RABBITMQ_PASSWORD = "guest"

EXCHANGE_NAME     = "events"              # Topic Exchange name
EXCHANGE_TYPE     = "topic"
QUEUE_NAME        = "event_queue"
BINDING_KEYS      = ["order.*", "user.#"] # Patterns the consumer subscribes to

# PostgreSQL
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "pipeline_db"
DB_USER     = "pipeline_user"
DB_PASSWORD = "secret"
```

> To add new event types (e.g. payment events), add `"payment.*"` to `BINDING_KEYS` and restart the consumer.

---

## Running the Pipeline

You need **two terminal windows** in WSL (use Windows Terminal tabs: `Ctrl+Shift+T`).

### Terminal 1 — Start the Consumer (keep it running)

```bash
cd /mnt/e/Rabitmq
source venv/bin/activate
python consumer/consumer.py
```

Expected output:
```
=== Consumer started ===
    Exchange      : events (topic)
    Queue         : event_queue
    Binding keys  : ['order.*', 'user.#']
    Broker        : localhost:5672
    Database      : pipeline_db @ localhost

[✔] PostgreSQL connection pool created.
  [~] Bound pattern 'order.*' → queue 'event_queue'
  [~] Bound pattern 'user.#'  → queue 'event_queue'

[*] Waiting for messages … (CTRL+C to stop)
```

### Terminal 2 — Run the Producer

```bash
cd /mnt/e/Rabitmq
source venv/bin/activate
python producer/producer.py
```

Expected output:
```
=== Producer started ===
    Exchange : events (topic)
    Broker   : localhost:5672

  [→] Published  [order.created      ]  {'order_id': 101, ...}
  [→] Published  [order.shipped      ]  {'order_id': 101, ...}
  [→] Published  [user.signup        ]  {'user_id': 2, ...}
  [→] Published  [user.login         ]  {'user_id': 2, ...}
  [→] Published  [order.canceled     ]  {'order_id': 102, ...}
  [→] Published  [order.created      ]  {'order_id': 103, ...}
  [→] Published  [payment.success    ]  {'order_id': 103, ...}

=== All messages published. Connection closed. ===
```

### Terminal 3 — Verify data in PostgreSQL

```bash
cd /mnt/e/Rabitmq
source venv/bin/activate
python db/verify.py
```

---

## Code Walkthrough

### `producer/producer.py`

```
1. sys.path.insert → allows importing config.py from project root
2. Create a RabbitMQ connection using pika.BlockingConnection
3. Declare the Topic Exchange (idempotent — safe to call multiple times)
4. For each sample message:
   a. Serialize payload to JSON
   b. Publish with basic_publish():
      - exchange      = "events"
      - routing_key   = e.g. "order.created"
      - delivery_mode = 2  (persistent — survives broker restart)
5. Close connection
```

---

### `consumer/consumer.py`

```
1. sys.path.insert → allows importing config.py from project root
2. Initialize a PostgreSQL connection pool (1–5 connections)
3. Connect to RabbitMQ
4. Declare the same Topic Exchange (idempotent)
5. Declare a durable queue ("event_queue")
6. Bind the queue to the exchange for each pattern in BINDING_KEYS
7. Set prefetch_count=1 (fair dispatch)
8. Start consuming:
   For each message received:
     a. Parse JSON body
     b. INSERT into events table (routing_key + payload)
     c. basic_ack()  → remove from queue after successful save
     d. basic_nack(requeue=True) on DB error → retry instead of dropping
```

**Key design decisions:**

| Decision | Why |
|----------|-----|
| `durable=True` queue | Messages survive RabbitMQ restart |
| `prefetch_count=1` | Fair load distribution across multiple consumers |
| `basic_ack` after DB write | No data loss — message only removed after save |
| `basic_nack(requeue=True)` on error | Transient DB failures don't silently drop messages |
| Connection pool | Reuses DB connections instead of opening one per message |

---

### `db/setup.py`

```
1. Connect as postgres superuser (via Unix socket — no password needed)
2. Create pipeline_user (if not exists)
3. Create pipeline_db database (if not exists)
4. Grant all privileges to pipeline_user
5. Connect to pipeline_db as pipeline_user
6. CREATE TABLE IF NOT EXISTS events (...)
```

---

## Database Schema

```sql
CREATE TABLE events (
    id          SERIAL       PRIMARY KEY,       -- Auto-incrementing ID
    routing_key VARCHAR(100) NOT NULL,          -- e.g. "order.created"
    payload     JSONB        NOT NULL,          -- Full message as queryable JSON
    received_at TIMESTAMPTZ  DEFAULT NOW()      -- Timestamp with timezone
);
```

### Why JSONB?

`JSONB` lets you query inside the JSON payload using SQL:

```sql
-- Find all orders over $100
SELECT * FROM events
WHERE routing_key = 'order.created'
  AND (payload->>'amount')::numeric > 100;

-- Find all events for a specific user
SELECT * FROM events
WHERE payload->>'user_id' = '2';

-- Count events by type
SELECT routing_key, COUNT(*) FROM events GROUP BY routing_key;
```

---

## Troubleshooting

### RabbitMQ won't start
```bash
sudo service rabbitmq-server restart
sudo journalctl -u rabbitmq-server -n 50
```

### PostgreSQL won't start
```bash
sudo service postgresql restart
sudo -u postgres pg_lsclusters
```

### `psycopg2-binary` build error (pg_config not found)
```bash
sudo apt install -y libpq-dev python3-dev
pip install -r requirements.txt
```

### `FATAL: password authentication failed for user "postgres"`
```bash
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
python db/setup.py
```

### Consumer not receiving messages
- Verify binding patterns in `config.py` match the routing keys the producer uses
- Check the RabbitMQ UI: http://localhost:15672 (guest/guest) → Queues tab

### Services don't auto-start after WSL restart
Add to `~/.bashrc`:
```bash
sudo service rabbitmq-server start 2>/dev/null
sudo service postgresql start 2>/dev/null
```

---

## What's Next

| Enhancement | How |
|-------------|-----|
| **Add payment events** | Add `"payment.*"` to `BINDING_KEYS` in `config.py` |
| **Multiple consumers** | Run `python consumer/consumer.py` in 2+ terminals — RabbitMQ round-robins |
| **Dead Letter Queue** | Route nacked messages to a DLQ for inspection instead of requeueing |
| **Docker Compose** | Package RabbitMQ + PostgreSQL + app into `docker-compose.yml` |
| **Retry with backoff** | Add exponential backoff on DB write failures in consumer |
| **Schema validation** | Validate message payloads with `pydantic` before saving |

---

## Credentials Reference

| Service | URL | User | Password |
|---------|-----|------|----------|
| RabbitMQ AMQP | localhost:5672 | guest | guest |
| RabbitMQ UI | http://localhost:15672 | guest | guest |
| PostgreSQL | localhost:5432 | pipeline_user | secret |
| PostgreSQL DB | — | — | pipeline_db |

---

## Quick Commands

```bash
# Start services
sudo service rabbitmq-server start
sudo service postgresql start

# Activate venv (run from project root)
cd /mnt/e/Rabitmq && source venv/bin/activate

# Run pipeline
python consumer/consumer.py     # Terminal 1 — keep running
python producer/producer.py     # Terminal 2 — publish messages
python db/verify.py             # Terminal 3 — check DB output

# One-time DB setup
python db/setup.py

# Service health
sudo rabbitmqctl status
sudo service postgresql status
```
