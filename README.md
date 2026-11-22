# Library Management System (LMS)

This repository contains the requirements, design, and source code of the Library Management System developed by Group 06 for the Software Engineering course.

The system supports counter borrowing and returning with barcode scanning, reservation queues, fines paid in cash at the counter, e-books, inventory checks, staff roles and permissions, password resets, an audit log, database backup, and daily automatic tasks. Version 1.0.0 implements every functional requirement in the specification. The full specification is in [`docs/Requirements_and_Design.md`](docs/Requirements_and_Design.md). The coding plan and the owner of each version are in [`CHANGELOG.md`](CHANGELOG.md).

## Getting Started

### Option 1: Docker (recommended)

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) on Windows or macOS, or Docker Engine on Linux.

```bash
git clone https://github.com/duypht07-SE/Library-Management-System.git
cd Library-Management-System
docker compose up --build
```

Open http://localhost:5000. The database is created with sample data on the first start.

| Task | Command |
|---|---|
| Start in the background | `docker compose up -d` |
| Stop | `docker compose down` |
| Run the tests | `docker compose run --rm web pytest` |
| Reset the database | `docker compose run --rm web python src/app.py --reset-db` |
| Delete the database volume | `docker compose down -v` |

The `src` and `tests` folders are mounted into the container. To see code changes after a page refresh while you develop, put `LMS_DEBUG=1` in `.env`; keep it `0` for a demo, because the debugger can run code. Run `docker compose up --build` again only after you change `requirements.txt` or the `Dockerfile`.

### Option 2: Python on your machine

You need Python 3.11 or newer.

**Windows (cmd):**

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src\app.py
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/app.py
```

Open http://127.0.0.1:5000. Run the tests with `pytest`. Reset the database with `python src/app.py --reset-db`.

### Sample Accounts

Every sample account uses the password `Library@123`. The sample Readers with a pending or locked card cannot sign in until a Librarian approves or unlocks the card.

| Role | Email | Status |
|---|---|---|
| Administrator | admin@library.test | Active |
| Librarian | librarian@library.test | Active, staff role Full Librarian |
| Reader | reader@library.test | Active, has a loan, a ready hold, and an unpaid fine |
| Reader | reader2@library.test | Active, has an overdue loan |
| Reader | reader3@library.test | Active |
| Reader | pending@library.test | Waiting for card approval |
| Reader | locked@library.test | Locked |

### Accounts and Roles

| Role | Pages |
|---|---|
| Guest | Home, Search Books, Book details, Library Policies, Help, Sign In, Create Account, Forgot Password |
| Reader | Guest pages, My Books (loans, reservations, renewals), Notifications, My Fines, E-Books, My Profile |
| Librarian | Depends on the staff role: Check Out and Check In (CIRCULATION), Reader Cards (READER_CARDS), Books, e-books, and Inventory (CATALOG), Fines (FINES); Password |
| Administrator | Librarians, Roles, Rules, Reports, Password Resets, Audit Log, Backups, Password |

The default staff roles are Full Librarian (every permission), Circulation Desk, and Catalog Librarian. The Administrator can add roles on the Roles page. Each page checks the role and the permission on the server, so typing a URL does not bypass access control. Sign-ins and every successful Librarian or Administrator action are written to the audit log. Five wrong passwords lock the account for 15 minutes, and a session ends after 30 minutes without activity; sessions are kept on the server and end at sign-out or after a password change. A temporary password from the Administrator works for 24 hours and must be changed at the first sign-in. Passwords need at least 8 characters with one letter and one digit. Every day at 00:00 the database is backed up to two folders, and the newest 30 daily backups are kept.

### Settings

The app reads these environment variables. Copy `.env.example` to `.env` to change them for Docker.

| Variable | Default | Meaning |
|---|---|---|
| `LMS_SECRET_KEY` | random | Key that signs the session cookie |
| `LMS_DEBUG` | `0` | Reload the server when code changes (development only) |
| `LMS_HOST` | `127.0.0.1` (`0.0.0.0` in Docker) | Server address |
| `LMS_PORT` | `5000` | Server port |
| `LMS_DB_PATH` | `instance/library.db` | SQLite database file |
| `LMS_SEED` | `1` | Load sample data when the database is created |
| `LMS_AVATAR_DIR` | `instance/avatars` | Folder for uploaded profile avatars |
| `LMS_EBOOK_DIR` | `instance/ebooks` | Folder for uploaded e-books (PDF, EPUB) |
| `LMS_BACKUP_DIR` | `instance/backups` | Folder for database backups |
| `LMS_BACKUP_COPY_DIR` | `instance/backups_copy` (a second volume in Docker) | Second folder for the daily backup (NFR-REL-04) |
| `LMS_BCRYPT_ROUNDS` | `12` | Bcrypt cost factor (NFR-SEC-01) |
| `LMS_SESSION_COOKIE_SECURE` | `0` | Set to `1` when the site uses HTTPS (automatic when HTTPS is on) |
| `LMS_SSL_CERT`, `LMS_SSL_KEY` | empty | Certificate and private key files; set both to serve HTTPS (NFR-SEC-02) |

### HTTPS

The server uses HTTPS with TLS 1.2 or 1.3 when `LMS_SSL_CERT` and `LMS_SSL_KEY` point to a certificate and its private key. The `certs/` folder is ignored by Git, so a private key is never committed. For a test certificate (Git Bash on Windows, or Linux):

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=localhost" -keyout certs/key.pem -out certs/cert.pem
```

- Docker: put `LMS_SSL_CERT=/app/certs/cert.pem` and `LMS_SSL_KEY=/app/certs/key.pem` in `.env`, run `docker compose up`, and open https://localhost:5000.
- Python: set `LMS_SSL_CERT=certs/cert.pem` and `LMS_SSL_KEY=certs/key.pem`, run `python src/app.py`, and open https://127.0.0.1:5000.

The browser warns about a self-signed certificate; a real deployment uses a certificate from a certificate authority.

## Architecture

The code follows a layered architecture with MVC in the presentation layer (NFR-MNT-01). Each layer only calls the layer below it.

| Layer | Folder | Content |
|---|---|---|
| Presentation | `src/presentation/` | Controllers (one class per role), Jinja templates (views), CSS, and JavaScript |
| Business | `src/business/` | Services that apply the library rules |
| Data | `src/data/` | `Database` (connection and transactions), repositories, `schema.sql`, `seed.sql` |
| Models | `src/models/` | Classes from the class diagram: `User` and its subclasses, `Book`, `BookCopy`, `BorrowRecord`, `Reservation`, `Fine`, `Notification`, `SystemConfig`; added in 1.0.0: `StaffRole`, `PasswordResetRequest`, `AuditLog`, `Ebook`, `InventoryCheck` |

```text
.
├── docs/                   # Specification, test cases, test report, test data
├── diagrams/               # DFD, use case, class diagram, ERD (draw.io and PNG)
├── ui/                     # Interface designs
├── src/
│   ├── app.py              # Entry point, builds LibraryApp
│   ├── config.py
│   ├── common/             # PasswordHasher, validation, CSRF
│   ├── models/
│   ├── data/
│   │   └── repositories/
│   ├── business/           # One service per feature (catalog, circulation, roles, ...)
│   └── presentation/
│       ├── templates/
│       └── static/
├── tests/                  # pytest
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── CHANGELOG.md
```

### Adding a Feature

1. Add or update the model in `src/models/` if a new field or rule is needed.
2. Add the SQL in a repository in `src/data/repositories/`.
3. Put the rule checks in a service in `src/business/`. Use `Database.transaction()` when the feature changes more than one row (NFR-REL-02).
4. Add a controller class in `src/presentation/` that extends `BaseController`, then register it in `LibraryApp._register_controllers`.
5. Add the template in `src/presentation/templates/`, extending `base.html`.
6. Add tests in `tests/`.

## Coding Rules

- Follow PEP 8: `CapWords` for classes, `snake_case` for functions and variables, `UPPER_CASE` for constants.
- Indent with 4 spaces. Keep lines at 80 characters or less.
- Give each class a one-line docstring. Add a comment only where the code is not clear, and cite the requirement ID (for example `# NFR-REL-02`).
- Raise an exception for invalid data and handle it in the layer that can recover. Pages never show a stack trace (404 and 500 pages).

## Testing

Run `pytest` (or `docker compose run --rm web pytest`) before every commit. All tests must pass before a pull request is merged (regression testing).

| File | Level | Content |
|---|---|---|
| `tests/test_models.py` | Unit | Each domain class, with equivalence partitions and boundary values |
| `tests/test_auth.py` | Unit | Input validation, login status, temporary lock, card actions |
| `tests/test_database.py` | Component | Schema, constraints, repositories, and transactions |
| `tests/test_accounts.py` | Component | Registration, login attempts, profiles, cards, staff, rules, migration |
| `tests/test_pages.py` | System | Guest pages through the Flask test client |
| `tests/test_auth_pages.py` | System | Sign in, roles, profile, avatar, reader cards, staff, rules, CSRF |
| `tests/test_catalog_fines_reports.py` | Component, System | Books, copies, search, fines, reports |
| `tests/test_circulation.py` | Component, System | Check out, check in, reservations, renewals, daily job |
| `tests/test_staff_roles.py`, `test_password_reset.py`, `test_audit_log.py`, `test_inventory.py`, `test_ebooks.py`, `test_backup.py` | Unit, Component, System | Features added in 1.0.0 |
| `tests/test_regressions.py` | Regression | One test for each defect fixed in release testing |
| `tests/test_temporary_password.py`, `test_session_revocation.py`, `test_date_formatting.py`, `test_daily_backup.py`, `test_https.py` | Unit, Component, System | NFR fixes in 1.0.1 |

Test names end with the requirement they check, for example `test_login_lock_nfr_sec_06`.

Manual test cases TC01 to TC105 are in [`docs/Test_Cases.xlsx`](docs/Test_Cases.xlsx), written with the course Testing Document Template. Test files for them are in [`docs/test_data/`](docs/test_data/). The results, the defects, and the requirement traceability are in [`docs/Test_Report.md`](docs/Test_Report.md). Defects are tracked as GitHub Issues.

## Tech Stack

| Component | Tool |
|---|---|
| Language | Python 3.11+ |
| Web framework | Flask |
| Front end | HTML5, CSS3, JavaScript |
| Database | SQLite 3 (NFR-DEV-03) |
| Testing | pytest |
| Packaging | Docker, Docker Compose |
| Diagrams | draw.io |
| Version control | Git and GitHub |

### Open Source Components

| Component | Use | License |
|---|---|---|
| Flask (with Werkzeug and Jinja2) | Web framework | BSD-3-Clause |
| bcrypt | Password hashing | Apache-2.0 |
| pytest | Unit testing | MIT |
| Noto Sans (Google Fonts) | Font | SIL Open Font License 1.1 |
| python:3.12-slim | Docker base image | PSF License |

All licenses allow use in this project without publishing changes.

## Group 06 — Team Members

| No. | Full Name | Responsibilities |
|:---:|---|---|
| 1 | Phạm Hồ Thanh Duy | Project Introduction, Functional Requirements, and Non-Functional Requirements |
| 2 | Võ Đức Thắng | Data Flow Diagrams (DFD Level 0 and Level 1) and Use Case Diagram |
| 3 | Lê Phước Sang | Class Diagram Design |
| 4 | Nguyễn Đức Tài | Data Model Design |
