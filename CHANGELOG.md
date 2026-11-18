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

## [0.3.0] - Planned: Books and Fines

**Owner: Sang**

- [ ] Books screen: add, edit, classify, and retire books and copies (FR-LIB-01 to FR-LIB-05). Class method: `Librarian.manage_book`.
- [ ] Search Books page by title, author, ISBN, or category (FR-GST-02).
- [ ] Book details page with available copies.
- [ ] `fine_service.py` for late, damaged, and lost fines (used by 0.4.0).
- [ ] Fines page for Readers and cash payment at the counter (FR-RDR-08, FR-LIB-13). Class methods: `Reader.view_fines`, `Librarian.record_fine`, `Librarian.record_payment`.
- [ ] Reports screen (FR-ADM-05). Class method: `Administrator.view_reports`.

## [0.4.0] - Planned: Borrowing and Returning

**Owner: Tài**

Each step runs as one transaction. Follow the status table in Section 6.5.

- [ ] Check Out screen (FR-LIB-06, FR-LIB-07). Class method: `Librarian.check_out`.
- [ ] Check In screen with condition and fines (FR-LIB-08, FR-LIB-09). Class method: `Librarian.check_in`.
- [ ] Reserve and cancel a reservation (FR-RDR-03). Class method: `Reader.reserve_book`.
- [ ] Renew a loan (FR-RDR-04, FR-RDR-05). Class method: `Reader.request_renewal`.
- [ ] My Books page (FR-RDR-06). Class method: `Reader.view_borrow_history`.
- [ ] Daily job at 00:00: mark overdue loans, cancel expired holds (FR-SYS-01, FR-SYS-03).
- [ ] In-app notifications (FR-SYS-02).

## [1.0.0] - Planned: Release

**Owner: Everyone**

- [ ] Each member retests their own version and fixes their bugs.
- [ ] Check that `docs/Test_Cases.xlsx` covers every use case in Section 4.3. Keep the Testing Document Template from Elearning 5 (a different template scores 0).
- [ ] Report bugs as GitHub Issues.
- [ ] Prepare demo data and run every use case in Section 4.
- [ ] Tag the release: `git tag v1.0.0`.

Not planned for 1.0.0: e-books, password reset, custom roles, inventory audit, backup and restore.
