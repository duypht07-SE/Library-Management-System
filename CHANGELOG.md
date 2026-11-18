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
2. Code your version. Tick each task below when it is done.
3. Run `pytest`. All tests must pass.
4. Open a pull request into `main`. The reviewer checks and merges it.
5. Change `Planned` to the merge date, then tell the next owner to start.

## [0.1.0] - Planned: Project Setup

**Owner: Thắng**

- [x] Flask app in layers (`models`, `data`, `business`, `presentation`) and Docker setup.
- [x] Database with the 8 tables from Section 6.4 and sample data.
- [x] Classes from the class diagram (`User`, `Reader`, `Librarian`, `Administrator`, `Book`, ...).
- [x] Guest pages: Home, Library Policies, Help, Loading, Page Not Found, and a 500 error page.
- [x] 64 pytest tests and a README with setup steps.

Fixed: a returned loan was counted as late when its status was not updated yet.

## [0.2.0] - Planned: Sign In and Accounts

**Owner: Duy**

- [ ] Create Account and Sign In pages (FR-GST-01, FR-GST-04).
- [ ] Lock the account for 15 minutes after 5 wrong passwords. End the session after 30 minutes (NFR-SEC-05, NFR-SEC-06).
- [ ] Check the role on every page, including typed URLs (NFR-SEC-03).
- [ ] Profile page for Readers (FR-RDR-02).
- [ ] Readers screen: approve, reject, lock, unlock cards (FR-LIB-10, FR-LIB-11).
- [ ] Librarian Accounts screen (FR-ADM-01).
- [ ] Rules screen: change the 5 rules without changing code (FR-ADM-04).

Tips: use `PasswordHasher` and `UserRepository.find_by_email`. Replace the `/signin` link in `base.html`. Until 0.4.0, send users to the Home page after sign in.

## [0.3.0] - Planned: Books and Fines

**Owner: Sang**

- [ ] Books screen: add, edit, classify, and retire books and copies (FR-LIB-01 to FR-LIB-05).
- [ ] Search Books page by title, author, ISBN, or category (FR-GST-02).
- [ ] Book details page with available copies.
- [ ] `fine_service.py` for late, damaged, and lost fines (used by 0.4.0).
- [ ] Fines page for Readers and cash payment at the counter (FR-RDR-08, FR-LIB-13).
- [ ] Reports screen (FR-ADM-05).

## [0.4.0] - Planned: Borrowing and Returning

**Owner: Tài**

Each step runs as one transaction. Follow the status table in Section 6.5.

- [ ] Check Out screen (FR-LIB-06, FR-LIB-07).
- [ ] Check In screen with condition and fines (FR-LIB-08, FR-LIB-09).
- [ ] Reserve and cancel a reservation (FR-RDR-03).
- [ ] Renew a loan (FR-RDR-04, FR-RDR-05).
- [ ] My Books page (FR-RDR-06).
- [ ] Daily job at 00:00: mark overdue loans, cancel expired holds (FR-SYS-01, FR-SYS-03).
- [ ] In-app notifications (FR-SYS-02).

## [1.0.0] - Planned: Release

**Owner: Everyone**

- [ ] Each member retests their own version and fixes their bugs.
- [ ] Write the test cases in Excel.
- [ ] Report bugs as GitHub Issues.
- [ ] Prepare demo data and run every use case in Section 4.
- [ ] Tag the release: `git tag v1.0.0`.

Not planned for 1.0.0: e-books, password reset, custom roles, inventory audit, backup and restore.
