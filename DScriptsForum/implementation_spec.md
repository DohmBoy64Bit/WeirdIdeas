# Roblox Script Hub -- Implementation Specification

## 1. Project Vision

Build a secure, modular forum and script hub using Python with
FastAPI/Flask and TailwindCSS.

### Core Goals

-   Full forum system with threads and posts\
-   Script hub similar UX to rscripts.net\
-   Admin validation workflow\
-   Responsive mobile design\
-   Modular architecture following PEP + DREY\
-   High security standards

------------------------------------------------------------------------

## 2. Technology Stack

### Backend

-   FastAPI (preferred) or Flask\
-   PostgreSQL + Redis\
-   SQLAlchemy 2.0 + Alembic\
-   Argon2 password hashing\
-   JWT cookies

### Frontend

-   TailwindCSS\
-   Jinja2\
-   Alpine.js

------------------------------------------------------------------------

## 3. Folder Structure

    project/
    ├── app/
    │   ├── routes/
    │   ├── services/
    │   ├── models/
    │   ├── schemas/
    │   ├── templates/
    │   └── static/
    ├── tests/
    └── docker/

### Structural Rules

-   Files \< 300 lines\
-   Routes only HTTP logic\
-   Services contain business logic\
-   Templates contain no logic

------------------------------------------------------------------------

## 4. Features

### Auth

-   Register with one-time code\
-   Login\
-   Password recovery\
-   JWT sessions

### Forum

-   Threads\
-   Posts\
-   Reputation\
-   Ranks

### Script Hub

-   Recent & trending\
-   Likes\
-   Downloads\
-   Admin validation\
-   Search

### User System

-   User CP\
-   Awards\
-   Roles

------------------------------------------------------------------------

## 5. Security

-   CSRF protection\
-   Rate limiting\
-   Input validation\
-   XSS sanitization\
-   CSP headers\
-   Audit logs

------------------------------------------------------------------------

## 6. Development Phases

1.  Foundation\
2.  Forum\
3.  Script Hub\
4.  Admin\
5.  Hardening

------------------------------------------------------------------------

## 7. Anti Feature-Creep Rules

-   Do not invent features\
-   Do not change stack\
-   Do not mix layers\
-   No raw SQL

------------------------------------------------------------------------

## 8. Deliverable Format

Each module must include: - Path\
- Purpose\
- Code\
- Tests\
- Security notes
