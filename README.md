# Library Management System (LMS)

This repository contains the requirements, design, and source code of the Library Management System developed by Group 06 for the Software Engineering course.

The system supports counter borrowing and returning with barcode scanning, reservation queues, fines paid in cash at the counter, and daily automatic tasks. The full specification is in [`docs/Requirements_and_Design.md`](docs/Requirements_and_Design.md). The coding plan and the owner of each version are in [`CHANGELOG.md`](CHANGELOG.md).

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

The `src` and `tests` folders are mounted into the container, so code changes show after a page refresh. Run `docker compose up --build` again only after you change `requirements.txt` or the `Dockerfile`.

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

Every sample account uses the password `Library@123`. Sign in is added in version 0.2.0.

| Role | Email | Status |
|---|---|---|
| Administrator | admin@library.test | Active |
| Librarian | librarian@library.test | Active |
| Reader | reader@library.test | Active, has a loan, a ready hold, and an unpaid fine |
| Reader | reader2@library.test | Active, has an overdue loan |
| Reader | reader3@library.test | Active |
| Reader | pending@library.test | Waiting for card approval |
| Reader | locked@library.test | Locked |

### Settings

The app reads these environment variables. Copy `.env.example` to `.env` to change them for Docker.

| Variable | Default | Meaning |
|---|---|---|
| `LMS_SECRET_KEY` | random | Key that signs the session cookie |
| `LMS_DEBUG` | `0` (`1` in Docker) | Reload the server when code changes |
| `LMS_HOST` | `127.0.0.1` (`0.0.0.0` in Docker) | Server address |
| `LMS_PORT` | `5000` | Server port |
| `LMS_DB_PATH` | `instance/library.db` | SQLite database file |
| `LMS_SEED` | `1` | Load sample data when the database is created |

## Architecture

The code follows a layered architecture with MVC in the presentation layer (NFR-MNT-01). Each layer only calls the layer below it.

| Layer | Folder | Content |
|---|---|---|
| Presentation | `src/presentation/` | Controllers (one class per role), Jinja templates (views), CSS, and JavaScript |
| Business | `src/business/` | Services that apply the library rules |
| Data | `src/data/` | `Database` (connection and transactions), repositories, `schema.sql`, `seed.sql` |
| Models | `src/models/` | Classes from the class diagram: `User` and its subclasses, `Book`, `BookCopy`, `BorrowRecord`, `Reservation`, `Fine`, `Notification`, `SystemConfig` |

```text
.
├── docs/                   # Requirements and design document
├── diagrams/               # DFD, use case, class diagram, ERD (draw.io and PNG)
├── ui/                     # Interface designs
├── src/
│   ├── app.py              # Entry point, builds LibraryApp
│   ├── config.py
│   ├── common/             # PasswordHasher
│   ├── models/
│   ├── data/
│   │   └── repositories/
│   ├── business/
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
| `tests/test_database.py` | Component | Schema, constraints, repositories, and transactions |
| `tests/test_pages.py` | System | Guest pages through the Flask test client |

Test names end with the requirement they check, for example `test_login_lock_nfr_sec_06`.

Manual test cases are in [`docs/Test_Cases.xlsx`](docs/Test_Cases.xlsx), written with the course Testing Document Template.

## Tech Stack

| Component | Tool |
|---|---|
| Language | Python 3.11+ |
| Web framework | Flask |
| Front end | HTML5, CSS3, JavaScript |
| Database | SQLite 3 (MySQL 8.0 planned for the demo) |
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
