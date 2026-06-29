# Baracoa Inventory Control System - Backend API (MVP)

A reliable, relational backend engine built with **FastAPI** and **SQLAlchemy** designed to manage warehouse logistics, physical inventory batches, transaction logs, and real-time business performance analytics.

## 🚀 Tech Stack
* **Framework:** FastAPI (Python 3.13)
* **ORM:** SQLAlchemy (Declarative Base Mapping)
* **Database Driver:** PyMySQL
* **Database Container:** MySQL 8.x (Dockerized)
* **Environment Configuration:** Python-Dotenv

---

## 📁 System Architecture

```text
/app
├── config.py         # Application settings & environment loader
├── database.py       # SQLAlchemy engine instance and session generator
├── main.py           # Application entry point & router orchestration
├── /models
│   ├── core.py       # Relational database models (MySQL schema definitions)
│   └── __init__.py   # Model package exposer
├── /routers
│   ├── categories.py # Inventory taxonomy management
│   ├── customers.py  # Consumer profiling logs
│   ├── inventory_batches.py # Physical stock arrivals & ledger hook
│   ├── loss_logs.py  # Waste management & alert metrics
│   ├── products.py   # Global item definitions
│   ├── reports.py    # Business intelligence & batch forensics
│   ├── sales.py      # Complex transaction processing engine
│   └── users.py      # Basic credentials management
└── /schemas
    ├── core.py       # Pydantic data validation layer & Enum constraints
    └── __init__.py   # Schema package mapping