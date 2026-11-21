# Changelog

Each member owns one version. The next member starts after the previous version is merged into `main`.

| Version | Owner | Content | Reviewer |
|---|---|---|---|
| 0.1.0 | Thắng | Project setup, database, Guest pages | Duy |
| 0.2.0 | Duy | Sign in, accounts, roles, rules | Sang |
| 0.3.0 | Sang | Books, search, fines, reports | Tài |
| 0.4.0 | Tài | Borrowing, returning, reservations, daily jobs | Thắng |
| 1.0.0 | Everyone | Testing, bug fixes, demo | Everyone |

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

- [x] 308 automated tests pass on Windows and in Docker.
- [x] Test cases TC01 to TC91 in `docs/Test_Cases.xlsx` (course template), with test data in `docs/test_data/`; TC37 to TC48, TC56, and TC58 now have exact input data.
- [x] Test results, defects, and requirement traceability in `docs/Test_Report.md`.
- [ ] Report each defect (D1 to D8) as a GitHub Issue.
- [ ] Tag the release after the merge: `git tag v1.0.0`.
