# Test Report — Releases 1.0.0 and 1.0.1

Library Management System, Group 06. Test dates: 21/11/2026 (1.0.0) and 22/11/2026 (1.0.1).

The tests follow the testing process in Chapter 5: design test cases → prepare test data → run the program with the test data → compare the results with the test cases → report.

| Item | Location |
|---|---|
| Test cases (course Testing Document Template) | [`docs/Test_Cases.xlsx`](Test_Cases.xlsx), TC01 to TC105 |
| Test data | [`docs/test_data/`](test_data/) and the sample data in `src/data/seed.sql` |
| Automated tests (pytest) | `tests/` |
| Defects | GitHub Issues, label `bug` (one issue per defect in Section 4) |

## 1. Test Environment

| Platform | Details |
|---|---|
| Docker (target) | Docker Engine 29 on WSL 2 (Kali Linux), image `python:3.12-slim`, `docker compose up --build` |
| Windows (host) | Windows 11, Python 3.14, `python src/app.py` |
| Browser | Google Chrome (desktop) |

## 2. Automated Tests (Development Testing)

`docker compose run --rm web pytest` and `pytest` on Windows: **362 passed, 0 failed** on both platforms (311 in 1.0.0).

| Level | Files | Tests |
|---|---|---|
| Unit: each class and method, equivalence partitions and boundary values | `test_models.py`, `test_auth.py` | 82 |
| Component: services, repositories, transactions | `test_database.py`, `test_accounts.py`, `test_catalog_fines_reports.py`, `test_circulation.py` | 82 |
| System: pages through the Flask test client | `test_pages.py`, `test_auth_pages.py` | 54 |
| 1.0.0 features (unit + component + system) | `test_staff_roles.py` 19, `test_password_reset.py` 18, `test_audit_log.py` 7, `test_inventory.py` 13, `test_ebooks.py` 18, `test_backup.py` 13 | 88 |
| Regression tests for the defects in Section 4 | `test_regressions.py` | 5 |
| 1.0.1 NFR fixes (unit + component + system) | `test_temporary_password.py` 16, `test_session_revocation.py` 16, `test_date_formatting.py` 2, `test_daily_backup.py` 8, `test_https.py` 9 | 51 |

Examples of partitions and boundaries that were tested:
- Role name of 1, 2, 50, and 51 characters.
- An e-book of exactly 20 MB, and one 5 bytes over.
- An empty barcode list, a list with one barcode, and a list with duplicates.
- Backup names containing `../` and `;`.
- The fine amount 0.

## 3. Manual Test Cases (Release Testing)

Every test case was run on the 1.0.0 build. The results matched the Expected Result column.

| Test cases | How they were run | Result |
|---|---|---|
| TC01–TC19 | Docker build, Chrome, and an HTTP script | Pass |
| TC20–TC36 | Docker build with an HTTP script (sign-in, lock, register, cards, rules, CSRF) and the system tests in `test_auth_pages.py` | Pass |
| TC37–TC48, TC56, TC58 (rewritten with exact data) | Script that executes each step and checks the expected message | Pass |
| TC49–TC63 | Docker build with an HTTP script and the system tests in `test_circulation.py` | Pass |
| TC64–TC92 (new in 1.0.0) | Script that executes each step and checks the expected message; Chrome for the screens | Pass |
| TC93–TC105 (new in 1.0.1) | Script for TC93–TC100, TC102, TC105; pytest for TC101 and TC103; TC104 on a live HTTPS server (TLS 1.3 negotiated, TLS 1.0 and 1.1 refused, HSTS header, Secure cookie) | Pass |

## 4. Defects Found and Fixed

| ID | Defect | Severity | Fix | Regression test |
|---|---|---|---|---|
| D1 | Check In showed "Enter valid numbers for loan and fine amount." for every error (for example an unknown barcode), because `ValidationError` is a `ValueError` and the wrong `except` came first | Medium | `except ValidationError` is now checked first | `test_bug1_*`, TC88 |
| D2 | A Reader could reserve a book they were borrowing; the reservation then blocked their own renewal. The Reserve Book button was also shown to a Reader who was borrowing or had already reserved the book | Medium | The server refuses the reservation with "You are already borrowing this book.", and the book page shows a note instead of the button | `test_bug2_*`, `test_reserve_button_hidden_*`, TC89 |
| D3 | Docker started Flask with the debugger on (`LMS_DEBUG=1`) on 0.0.0.0, so anyone on the network could reach the Werkzeug debugger | High | Default `LMS_DEBUG=0`; debug only through `.env` | TC17, E2E check |
| D4 | With the debug reloader the daily job thread started twice, and a 00:00 run was lost when the server was off at midnight | Medium | Start the job only in the serving process and run it once at start-up (the job is idempotent) | TC91 |
| D5 | Requirements FR-GST-05, FR-RDR-07, FR-LIB-12, FR-LIB-14, FR-ADM-02, FR-ADM-03, FR-ADM-06, FR-ADM-07, FR-ADM-08, and the action log of FR-SYS-04 were not implemented; the Help page pointed to a "Forgot password?" link that did not exist | High | Implemented in 1.0.0 (Section 5) | TC64–TC87 |
| D6 | In forms, a button placed directly in the form stretched to the full width (Reports, Backups), and the Add Copy form on Books was pushed to the right | Low | CSS fix | Checked in Chrome |
| D7 | 26 source lines were longer than 80 characters (coding rule, Chapter 4) | Low | Lines wrapped | Line check in the release checklist |
| D8 | TC56 and TC58 could not pass with the sample data, TC19 expected 78 tests, and TC37–TC48 had no exact input data | Low | Test cases rewritten | — |
| D9 | NFR-SEC-05: a temporary password never expired | Medium | 1.0.1 (Duy): 24-hour expiry checked at sign-in, during a session, and at password change; server-side sessions revoked at sign-out and password change | `test_temporary_password.py`, `test_session_revocation.py`, TC93–TC96 |
| D10 | NFR-COM-03: My Books, Check Out, Check In, Fines, and Password Resets showed dates as YYYY-MM-DD | Low | 1.0.1 (Sang): Jinja filter `date_vn` | `test_date_formatting.py`, TC97, TC98 |
| D11 | NFR-REL-04: no automatic daily backup and no second copy | Medium | 1.0.1 (Tài): backup at 00:00 to two folders, newest 30 kept | `test_daily_backup.py`, TC99, TC101, TC102 |
| D12 | NFR-SEC-02: the server could not use HTTPS | Medium | 1.0.1 (Thắng): `LMS_SSL_CERT` and `LMS_SSL_KEY`, HSTS header, Secure cookie | `test_https.py`, TC104, TC105 |
| D13 | A database error (for example "database is locked") during the daily backup stopped the whole daily job; at 00:00 the scheduler thread ended, so overdue marking and reminders stopped until a restart | High | Database errors are caught and written to the audit log; the scheduler uses `run_safely()` | `test_sqlite_error_*`, `test_run_safely_*`, TC103 |
| D14 | Every start-up made one more daily backup, so "keep 30" kept 30 runs instead of 30 days | Medium | At most one daily backup per day; a missing second copy is made on the next run | `test_restart_on_same_day_*`, `test_missing_copy_*`, TC100 |


## 5. Requirements Traceability

Each functional requirement has at least one test case and at least one automated test.

| Requirement | Test cases | Automated tests |
|---|---|---|
| FR-GST-01 Register | TC20–TC22 | `test_auth_pages.py`, `test_accounts.py` |
| FR-GST-02 Search | TC03–TC08, TC42, TC43 | `test_pages.py`, `test_catalog_fines_reports.py` |
| FR-GST-03 Library information | TC01, TC02, TC09, TC13 | `test_pages.py` |
| FR-GST-04 Log in | TC23–TC26, TC90 | `test_auth.py`, `test_auth_pages.py` |
| FR-GST-05 Request password reset | TC64, TC65 | `test_password_reset.py` |
| FR-RDR-01 Guest functions | TC42, TC56 | `test_pages.py` |
| FR-RDR-02 Profile | TC28–TC30 | `test_auth_pages.py` |
| FR-RDR-03 Reserve, cancel | TC56, TC57, TC89 | `test_circulation.py`, `test_regressions.py` |
| FR-RDR-04, FR-RDR-05 Renew | TC58, TC59 | `test_circulation.py` |
| FR-RDR-06 Borrowing history | TC60 | `test_circulation.py` |
| FR-RDR-07 Read e-books | TC81–TC83 | `test_ebooks.py` |
| FR-RDR-08 View fines | TC44 | `test_catalog_fines_reports.py` |
| FR-LIB-01 to FR-LIB-05 Books and copies | TC37–TC41, TC92 | `test_catalog_fines_reports.py` |
| FR-LIB-06, FR-LIB-07 Check out | TC49–TC51 | `test_circulation.py` |
| FR-LIB-08, FR-LIB-09 Check in, fines | TC46, TC52–TC55, TC88 | `test_circulation.py`, `test_regressions.py` |
| FR-LIB-10, FR-LIB-11 Reader cards | TC31, TC32 | `test_accounts.py`, `test_auth_pages.py` |
| FR-LIB-12 Inventory check | TC75–TC77 | `test_inventory.py` |
| FR-LIB-13 Cash payment | TC45 | `test_catalog_fines_reports.py` |
| FR-LIB-14 Manage e-books | TC78–TC80 | `test_ebooks.py` |
| FR-ADM-01 Librarian accounts | TC33, TC34 | `test_accounts.py` |
| FR-ADM-02 Roles and permissions | TC71–TC74 | `test_staff_roles.py` |
| FR-ADM-03 Reset passwords | TC66–TC70 | `test_password_reset.py` |
| FR-ADM-04 Rules | TC10, TC35 | `test_accounts.py`, `test_pages.py` |
| FR-ADM-05 Reports and export | TC47 | `test_catalog_fines_reports.py` |
| FR-ADM-06 Backup | TC85 | `test_backup.py` |
| FR-ADM-07 Restore | TC86, TC87 | `test_backup.py` |
| FR-ADM-08 Audit log | TC84 | `test_audit_log.py` |
| FR-SYS-01 Overdue scan | TC61, TC91 | `test_circulation.py` |
| FR-SYS-02 Notifications | TC53, TC60, TC61 | `test_circulation.py` |
| FR-SYS-03 Expired holds | TC62 | `test_circulation.py` |
| FR-SYS-04 Permission checks and action log | TC27, TC48, TC63, TC73, TC84 | `test_staff_roles.py`, `test_audit_log.py` |

Non-functional requirements fixed in 1.0.1:

| Requirement | Test cases | Automated tests |
|---|---|---|
| NFR-SEC-02 HTTPS with TLS 1.2 or 1.3 | TC104, TC105 | `test_https.py` |
| NFR-SEC-05 Session timeout, temporary password expiry | TC93–TC96 | `test_temporary_password.py`, `test_session_revocation.py` |
| NFR-COM-03 Dates as DD/MM/YYYY | TC97, TC98 | `test_date_formatting.py` |
| NFR-REL-04 Daily backup in two places | TC99–TC103 | `test_daily_backup.py` |
