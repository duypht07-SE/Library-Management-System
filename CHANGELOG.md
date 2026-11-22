# Changelog

Each member owns one version. The next member starts after the previous version is merged into `main`.

| Version | Owner | Content | Reviewer |
|---|---|---|---|
| 0.1.0 | Thắng | Project setup, database, Guest pages | Duy |
| 0.2.0 | Duy | Sign in, accounts, roles, rules | Sang |
| 0.3.0 | Sang | Books, search, fines, reports | Tài |
| 0.4.0 | Tài | Borrowing, returning, reservations, daily jobs | Thắng |
| 1.0.0 | Everyone | Testing, bug fixes, demo | Everyone |
| 1.0.1 | Duy, Sang, Tài, Thắng (in parallel) | Code fixes for 4 NFRs | Thắng |
| 1.0.2 | Thắng | UI review in Chrome and display fixes | Duy |

## How to Work

1. `git pull origin main`, then create a branch: `git checkout -b v0.2.0`.
2. Code your version. Every screen needs a GUI page, and every class method in the class diagram must exist in the code with the same name (in snake_case). Tick each task below when it is done.
3. Add test cases for your screens to `docs/Test_Cases.xlsx` (Testing Document Template, same columns, next TC number). Run `pytest`. All tests must pass.
4. Open a pull request into `main`. The reviewer checks and merges it.
5. Change `Planned` to the merge date, then tell the next owner to start.

## [0.1.0] - 2026-11-18: Project Setup

**Owner: Thắng**

- [x] Flask app in layers (`models`, `data`, `business`, `presentation`) and Docker setup.
- [x] Database with the 8 tables from Section 6.4 and sample data.
- [x] Classes from the class diagram with their methods: `renew`, `is_overdue`, `cancel`, `mark_paid`, `send`, `update_status`, `update`, `search`.
- [x] Guest pages: Home, Library Policies, Help, Loading, Page Not Found, and a 500 error page.
- [x] 78 pytest tests, test cases TC01 to TC19 in `docs/Test_Cases.xlsx`, and a README with setup steps.

Fixed: a returned loan was counted as late when its status was not updated yet.

## [0.2.0] - 2026-11-18: Sign In and Accounts

**Owner: Duy** · Status: complete on `feature/v0.2.0-auth`, waiting for reviewer Sang.

- [x] Create Account and Sign In pages (FR-GST-01, FR-GST-04). Class methods: `User.login`, `User.logout`, `User.update_profile`.
- [x] Lock the account for 15 minutes after 5 wrong passwords. End the session after 30 minutes (NFR-SEC-05, NFR-SEC-06).
- [x] Check the role on every page, including typed URLs (NFR-SEC-03). Guest, Reader, Librarian, and Administrator each have their own pages.
- [x] Profile page for Readers with name, Student/Staff ID, email, phone, avatar, and password (FR-RDR-02).
- [x] Readers screen: approve, reject, lock, unlock cards (FR-LIB-10, FR-LIB-11). Class methods: `Librarian.approve_card`, `Librarian.reject_card`, `Librarian.lock_reader`, `Librarian.unlock_reader`.
- [x] Librarian Accounts screen: create, edit, lock, unlock (FR-ADM-01). Class method: `Administrator.manage_librarian`.
- [x] Rules screen: change the 5 rules without changing code (FR-ADM-04). Class method: `Administrator.configure_rules`.
- [x] CSRF token for every form; server-side validation; Bcrypt hashes from the configured cost (NFR-SEC-01, NFR-SEC-07).
- [x] Database: add `users.student_id` and `users.avatar_path`, with an automatic `ALTER TABLE` for databases made by 0.1.0.
- [x] 100 new pytest tests (178 total, 0 failed) and manual test cases TC20 to TC36.

Note: run `python src/app.py --reset-db` to load the new sample Student/Staff IDs into an existing 0.1.0 database.

## [0.3.0] - 2026-11-18: Books and Fines

**Owner: Sang**

- [x] Books screen: add, edit, classify, and retire books and copies (FR-LIB-01 to FR-LIB-05). Class method: `Librarian.manage_book`.
- [x] Search Books page by title, author, ISBN, or category (FR-GST-02).
- [x] Book details page with available copies.
- [x] `fine_service.py` for late, damaged, and lost fines (used by 0.4.0).
- [x] Fines page for Readers and cash payment at the counter (FR-RDR-08, FR-LIB-13). Class methods: `Reader.view_fines`, `Librarian.record_fine`, `Librarian.record_payment`.
- [x] Reports screen (FR-ADM-05). Class method: `Administrator.view_reports`.

## [0.4.0] - 2026-11-19: Borrowing and Returning

**Owner: Tài**

Each step runs as one transaction. Follow the status table in Section 6.5.

- [x] Check Out screen (FR-LIB-06, FR-LIB-07). Class method: `Librarian.check_out`.
- [x] Check In screen with condition and fines (FR-LIB-08, FR-LIB-09). Class method: `Librarian.check_in`.
- [x] Reserve and cancel a reservation (FR-RDR-03). Class method: `Reader.reserve_book`.
- [x] Renew a loan (FR-RDR-04, FR-RDR-05). Class method: `Reader.request_renewal`.
- [x] My Books page (FR-RDR-06). Class method: `Reader.view_borrow_history`.
- [x] Daily job at 00:00: mark overdue loans, cancel expired holds (FR-SYS-01, FR-SYS-03).
- [x] In-app notifications (FR-SYS-02).

## [1.0.0] - 2026-11-21: Release

**Owner: Everyone**

Added, so that every functional requirement in the specification is implemented:

- [x] Staff roles and permissions: Roles page, a role for each Librarian, and a permission check on every Librarian page (FR-ADM-02, FR-SYS-04). Class: `StaffRole`.
- [x] Forgot Password page (FR-GST-05); Password Resets page where the Administrator gives a temporary password that must be changed at the next sign-in (FR-ADM-03). Class: `PasswordResetRequest`.
- [x] Audit log of sign-ins and every successful Librarian or Administrator action (FR-SYS-04, FR-ADM-08). Class: `AuditLog`.
- [x] Inventory check: scan the barcodes on a shelf and compare them with the catalog (FR-LIB-12). Class: `InventoryCheck`.
- [x] E-books: upload, update, and remove PDF or EPUB files (FR-LIB-14); Readers read a PDF online or download the file (FR-RDR-07). Class: `Ebook`.
- [x] Backup and restore of the database, with an automatic backup before every restore (FR-ADM-06, FR-ADM-07).
- [x] Change Password page for Librarians and Administrators.
- [x] Database: tables `staff_roles`, `permissions`, `role_permissions`, `ebooks`, `password_reset_requests`, `audit_logs`, and columns `users.staff_role_id`, `users.must_change_password`. An older database is upgraded on start.

Fixed (defects D1 to D8 in `docs/Test_Report.md`):

- [x] Check In showed the same "Enter valid numbers" message for every error.
- [x] A Reader could reserve a book they were borrowing; the Reserve Book button is now hidden when the Reader borrows or has reserved the book.
- [x] Docker started with the Flask debugger on; `LMS_DEBUG` is now `0` by default.
- [x] The daily job could run twice in debug mode and skipped a missed 00:00 run.
- [x] Form buttons stretched to the full width; the Add Copy form was misaligned.
- [x] Lines longer than 80 characters.

Testing:

- [x] 311 automated tests pass on Windows and in Docker.
- [x] Test cases TC01 to TC92 in `docs/Test_Cases.xlsx` (course template), with test data in `docs/test_data/`; TC37 to TC48, TC56, and TC58 now have exact input data.
- [x] Test results, defects, and requirement traceability in `docs/Test_Report.md`.
- [x] Report each defect (D1 to D8) as a GitHub Issue (#16 to #23, closed by PR #24).
- [x] Tag the release after the merge: `git tag v1.0.0`.

## [1.0.1] - 2026-11-22: NFR Fixes

**Owners: Duy, Sang, Tài, Thắng (in parallel, separate branches) · Reviewer, test cases, and release: Thắng**

Only the code changes. The specification (`docs/Requirements_and_Design.md`), the submitted Word file, the diagrams in `diagrams/`, and the images in `ui/` stay as they are.

Rules:

1. Branch from the newest `main`: `fix/1.0.1-duy`, `fix/1.0.1-sang`, `fix/1.0.1-tai`, `fix/1.0.1-thang`.
2. **Do not edit `docs/Test_Cases.xlsx`** (binary file, merge conflicts). Write new test cases (Function, Test Steps, Input Data, Expected Result) in the pull request description. Thắng adds them to the Excel file.
3. Add pytest tests for every change. All tests must pass before the pull request.
4. Lines of 80 characters or less. Keep the layered structure: model, repository, service, controller, template.

### Duy: NFR-SEC-05, temporary password expires after 24 hours

- [x] Add the column `users.temp_password_issued_at` (DATETIME; expiry = issued time + 24 hours) in `schema.sql` and in the migration in `database.py` (`_add_missing_columns`).
- [x] `PasswordResetService._reset` and `UserRepository.set_temporary_password`: save the issue time. `update_password` clears it.
- [x] `AuthService.authenticate`: a temporary password after its expiry time is refused with "This temporary password has expired. Please ask the library for a new one." An open session also ends when it expires.
- [x] pytest: sign-in at 23:59 after the reset works, at 24:01 is refused (boundary values); a normal password is never affected.
- [x] Extra: server-side sessions (`user_sessions`), revoked at sign-out and password change, 30-minute sliding window (NFR-SEC-05).

### Sang: NFR-COM-03, dates as DD/MM/YYYY

- [x] Add a Jinja filter `date_vn` in `app.py` that turns a `datetime` or a text like `2026-11-16 10:00:00` into `16/11/2026` (and `16/11/2026 10:00` when the time is needed).
- [x] Use it in `reader/my_books.html`, `librarian/checkout.html`, `librarian/checkin.html`, `librarian/fines.html`, and `admin/password_resets.html` (they show `2026-11-16` today).
- [x] pytest: the filter with a `datetime`, a text date, an empty value; My Books shows `DD/MM/YYYY`.

### Tài: NFR-REL-04, daily backup in two places

- [x] `DailyJobService.run` also calls `BackupService.create(label="daily")` at 00:00 and copies the file to a second folder `LMS_BACKUP_COPY_DIR` (`config.py`, `.env.example`, a second Docker volume in `docker-compose.yml`).
- [x] Keep the newest 30 daily backups in each folder; never delete manual or `auto` backups.
- [x] A failed copy is written to the audit log and does not stop the other daily tasks (NFR-REL-06).
- [x] pytest: one run makes one backup in each folder; 31 runs keep 30.

### Thắng: NFR-SEC-02 HTTPS, review, and release

- [x] Read `LMS_SSL_CERT` and `LMS_SSL_KEY` in `config.py`; when both are set, `LibraryApp.run` uses `ssl_context=(cert, key)`, `SESSION_COOKIE_SECURE` is on, and every response has a `Strict-Transport-Security` header. A missing file or a missing key stops the start with a clear message. `certs/` is ignored by Git. README explains how to make a test certificate.
- [x] Review the merged changes; run `pytest` and `docker compose up --build`.
- [x] Fixed in review: a database error during the daily backup stopped the whole daily job (D13); every start-up made one more daily backup (D14); 5 lines over 80 characters and 5 files without a final newline; a pytest collection warning.
- [x] Add the new test cases to `docs/Test_Cases.xlsx` (TC93 to TC105) and update `docs/Test_Report.md` (D9 to D14, NFR traceability, 362 tests).
- [x] Tag `v1.0.1` and create the GitHub Release.

## [1.0.2] - 2026-11-22: UI Review

**Owner: Thắng · Reviewer: Duy**

Every page was opened in Chrome with each role (Guest, Reader, Librarian, Administrator), with error and success messages, and the Guest and Reader pages also at 360 px. A script on each page checked for sideways scrolling, elements outside the screen, broken images, YYYY-MM-DD dates, leftover template text, clipped text, and JavaScript errors. No such problem was found. Fixed:

- [x] UI-1: the Reader menu on a 360 px phone took 238 px; smaller menu buttons under 760 px (206 px) (NFR-USA-04).
- [x] UI-2: Check Out errors now say what is wrong and what to do next, for example "Reader has unpaid fines of 15,000 VND. Record the cash payment on the Fines page first." (NFR-USA-03).
- [x] UI-3: space above headings on Fines and Book details.
- [x] UI-4: temporary passwords no longer use look-alike characters (0/O/o, 1/l/I).
- [x] Test cases TC106 (360 px pages) and TC107 (Check Out messages); 364 automated tests pass on Windows and in Docker.
- [ ] Tag `v1.0.2` and create the GitHub Release.
