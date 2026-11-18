# 🐇 RabbitMQ → PostgreSQL Pipeline — Progress Tracker

> Status: ✅ Done | 🔄 In Progress | ❌ Error | ⏳ Pending

---

## Phase 1 — Infrastructure Setup

| # | Step | Command / Action | Status | Notes |
|---|------|-----------------|--------|-------|
| 1 | Update WSL packages | `sudo apt update && sudo apt upgrade -y` | ✅ Done | |
| 2 | Install Erlang | `sudo apt install -y erlang` | ✅ Done | |
| 3 | Install RabbitMQ | `sudo apt install -y rabbitmq-server` | ✅ Done | |
| 4 | Start RabbitMQ | `sudo service rabbitmq-server start` | ✅ Done | Running on localhost:5672 |
| 5 | Enable Management UI | `sudo rabbitmq-plugins enable rabbitmq_management` | ✅ Done | UI at http://localhost:15672 |
| 6 | Install PostgreSQL | `sudo apt install -y postgresql postgresql-contrib` | ✅ Done | v18 installed |
| 7 | Start PostgreSQL | `sudo service postgresql start` | ✅ Done | Running on localhost:5432 |

---

## Phase 2 — Python Environment

| # | Step | Command / Action | Status | Notes |
|---|------|-----------------|--------|-------|
| 8 | Navigate to project | `cd /mnt/e/Rabitmq` | ✅ Done | |
| 9 | Create virtual env | `python3 -m venv venv` | ✅ Done | |
| 10 | Activate venv | `source venv/bin/activate` | ✅ Done | |
| 11 | Fix psycopg2 deps | `sudo apt install -y libpq-dev python3-dev` | ✅ Done | Required for Python 3.14 |
| 12 | Install requirements | `pip install -r requirements.txt` | ✅ Done | |

---

## Phase 3 — Database Setup

| # | Step | Command / Action | Status | Notes |
|---|------|-----------------|--------|-------|
| 13 | Run DB setup script | `python db/setup.py` | ✅ Done | pipeline_db, pipeline_user, events table created |
| 14 | Verify table created | `psql -U pipeline_user -d pipeline_db -h localhost -c "\d events"` | ✅ Done | |

---

## Phase 4 — Run the Pipeline

| # | Step | Terminal | Command | Status | Notes |
|---|------|----------|---------|--------|-------|
| 15 | Start consumer | Terminal 1 | `python consumer/consumer.py` | ✅ Done | Listening on order.* and user.# |
| 16 | Publish messages | Terminal 2 | `python producer/producer.py` | ✅ Done | 6 of 7 messages routed & saved |
| 17 | Verify data in DB | Terminal 3 | `python db/verify.py` | ✅ Done | 6 events confirmed in PostgreSQL |

---

## Phase 5 — Restructure Project

| # | Step | Action | Status | Notes |
|---|------|--------|--------|-------|
| 18 | Create `producer/` package | `producer/__init__.py` + `producer/producer.py` | ✅ Done | sys.path set to find root config.py |
| 19 | Create `consumer/` package | `consumer/__init__.py` + `consumer/consumer.py` | ✅ Done | sys.path set to find root config.py |
| 20 | Create `db/` package | `db/__init__.py` + `db/setup.py` + `db/verify.py` | ✅ Done | Renamed db_setup.py → db/setup.py |
| 21 | Create `docs/` folder | Moved `project_requirement.md` → `docs/` | ✅ Done | |
| 22 | Remove old root scripts | Deleted producer.py, consumer.py, db_setup.py, verify.py | ✅ Done | |
| 23 | Update README paths | All commands now use new folder paths | ✅ Done | |

---

## 🏁 Final Verification Output

```
ID    ROUTING KEY            RECEIVED AT                       PAYLOAD
──────────────────────────────────────────────────────────────────────────────
1     order.created          2026-11-18 14:04:18.940135+00:00  {"amount": 299.99, ...}
2     order.shipped          2026-11-18 14:04:19.441923+00:00  {"carrier": "DHL", ...}
3     user.signup            2026-11-18 14:04:19.942193+00:00  {"plan": "free", ...}
4     user.login             2026-11-18 14:04:20.444754+00:00  {"ip": "192.168.1.10", ...}
5     order.canceled         2026-11-18 14:04:20.945497+00:00  {"reason": "out of stock", ...}
6     order.created          2026-11-18 14:04:21.446198+00:00  {"amount": 49.0, ...}

  Total: 6 event(s)
```

> ℹ️ `payment.success` was intentionally NOT saved — no binding pattern matches it. Correct Topic Exchange behaviour.

---

## 🛠️ Fix Log

### ❌ Step 12 — psycopg2-binary build error (Python 3.14)
**Error:** `pg_config executable not found`
**Fix:** `sudo apt install -y libpq-dev python3-dev` → retry pip install. ✅ Resolved

### ❌ Step 13 — db_setup.py postgres auth error
**Error:** `FATAL: password authentication failed for user "postgres"`
**Fix:** `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"` → retry db/setup.py. ✅ Resolved

---

## 📁 Final Project Structure

```
e:\Rabitmq\
├── config.py                   ← Central config (all credentials & settings)
├── requirements.txt            ← Python dependencies
├── README.md                   ← Full documentation
├── PROGRESS.md                 ← This file
├── producer\
│   ├── __init__.py
│   └── producer.py             ← Publishes events to RabbitMQ
├── consumer\
│   ├── __init__.py
│   └── consumer.py             ← Saves events to PostgreSQL
├── db\
│   ├── __init__.py
│   ├── setup.py                ← One-time DB/table creation
│   └── verify.py               ← Check events in DB
├── docs\
│   └── project_requirement.md ← Original requirements
└── venv\                       ← Python virtual environment (not committed)
```

---

## 🔑 Credentials Reference

| Service | Host | Port | User | Password | DB |
|---------|------|------|------|----------|----|
| RabbitMQ | localhost | 5672 | guest | guest | — |
| RabbitMQ UI | localhost | 15672 | guest | guest | — |
| PostgreSQL | localhost | 5432 | pipeline_user | secret | pipeline_db |

---

## ✅ Quick Commands (updated paths)

```bash
# Start services
sudo service rabbitmq-server start
sudo service postgresql start

# Activate venv (always from project root)
cd /mnt/e/Rabitmq && source venv/bin/activate

# One-time DB setup
python db/setup.py

# Run pipeline
python consumer/consumer.py     # Terminal 1 — keep running
python producer/producer.py     # Terminal 2 — publish messages
python db/verify.py             # Terminal 3 — check DB output
```
