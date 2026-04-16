# Project Analysis — Heuristics Guide

## 1. Language Detection

| Signal | Language |
|--------|----------|
| Files with `.py` extension | Python |
| Files with `.js` or `.ts` extension (no `.py`) | JavaScript/TypeScript (Node.js) |
| `package.json` present | Node.js project |
| `requirements.txt` or `pyproject.toml` present | Python project |
| `go.mod` present | Go |
| `pom.xml` or `build.gradle` present | Java |

## 2. Framework Detection

### Python
| Signal | Framework |
|--------|-----------|
| `from flask import Flask` or `import flask` | Flask |
| `from django.` imports | Django |
| `from fastapi import FastAPI` | FastAPI |
| Version: check `requirements.txt` for `Flask==x.x.x` | Flask version |
| `Flask-SQLAlchemy` in requirements | Uses SQLAlchemy ORM |
| `flask-cors` in requirements | CORS enabled |

### Node.js
| Signal | Framework |
|--------|-----------|
| `require('express')` or `import express` | Express.js |
| `require('fastify')` | Fastify |
| `require('koa')` | Koa |
| Version: check `package.json` `dependencies` field | Framework version |
| `require('sqlite3')` | SQLite3 (callback-based) |
| `require('sequelize')` | Sequelize ORM |
| `require('mongoose')` | MongoDB/Mongoose |

## 3. Database Detection

| Signal | Database |
|--------|----------|
| `sqlite3.connect(...)` or `sqlite3.Database(...)` | SQLite |
| `psycopg2` or `pg` in dependencies | PostgreSQL |
| `pymysql` or `mysql2` in dependencies | MySQL |
| `mongoose` or `pymongo` in dependencies | MongoDB |
| `CREATE TABLE` in source files | Raw SQL |
| `db.Model` or `db.Column` (SQLAlchemy) | ORM models |

## 4. Architecture Detection

### Monolithic (all-in-one)
- Single file or 2-3 files contain routes, business logic, and data access
- No separation between concerns
- Example: `app.py` contains route handlers AND SQL queries AND business rules

### Layered (partial MVC)
- Some separation exists but incomplete
- Models exist but controllers have business logic
- Routes import from models directly
- Missing: proper controllers layer OR missing: config separation

### MVC-complete
- Clear `models/`, `controllers/`, `routes/` directories
- Config in separate module
- Entry point (`app.py` or `index.js`) only wires things together

### God Class / God File
- One class or file handles multiple domains
- Signs: >300 lines in a single file with multiple unrelated functions
- Signs: class methods mixing HTTP handling, SQL queries, and business rules

## 5. Domain Detection

Read the route paths, table names, and function names to determine the application domain:
- `/produtos`, `/pedidos`, `/usuarios` → E-commerce API
- `/tasks`, `/users`, `/categories` → Task Manager
- `/courses`, `/enrollments`, `/checkout` → LMS (Learning Management System)
- `/orders`, `/products`, `/cart` → Shopping platform

## 6. File Inventory

Count and categorize:
- Entry point files (`app.py`, `index.js`, `main.py`)
- Model files
- Controller/handler files
- Route files
- Utility/helper files
- Config files
- Test files
- Configuration files (`requirements.txt`, `package.json`, `.env`)

## 7. Database Tables / Models Mapping

- Look for `CREATE TABLE` statements
- Look for `db.Model` subclasses (SQLAlchemy)
- Look for `db.run("CREATE TABLE ...")` (Node.js SQLite)
- List all tables/models found with their key fields
