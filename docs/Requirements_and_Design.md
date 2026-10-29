
# Software Requirements Specification and Design Document

**Project Name:** Library Management System (LMS)

## 1. Functional Requirements

### 1.1 Overview

The Library Management System (LMS) supports the main operations of a library: managing books and readers, borrowing and returning books, reserving books that are not available, and viewing statistics.

**Users**

- **Guest**: a person who is not logged in. A Guest can search books and register a Reader account.
- **Reader**: a registered library member.
- **Librarian**: library staff who manage books, readers, and borrowing.
- **Administrator**: the person who manages Librarian accounts and system permissions.

**Conventions**

- The word **"shall"** indicates a mandatory requirement.
- Requirement IDs use the format `FR-<GROUP>-<NN>`; business rules use `BR-<NN>`.

---

### 1.2 Book Management

| ID | Requirement |
|---|---|
| FR-BOOK-01 | The system shall allow a Librarian to add a new book. Each book shall have a unique book ID, title, author, category, publication year, total number of copies, and an optional cover image. |
| FR-BOOK-02 | The system shall allow a Librarian to update the information of an existing book. |
| FR-BOOK-03 | The system shall allow a Librarian to delete a book only if the book has no active borrowing records. |
| FR-BOOK-04 | The system shall keep track of the total copies and the number of available copies of each book. |

### 1.3 Book Searching, Browsing, and Sorting

| ID | Requirement |
|---|---|
| FR-SRC-01 | The system shall allow users to search for a book by book ID. |
| FR-SRC-02 | The system shall allow users to search for books by title. The search shall support substring matching (the result contains every book whose title includes the entered text). |
| FR-SRC-03 | The system shall allow users to search for books by author. |
| FR-SRC-04 | The system shall allow users to list the books of a selected category. |
| FR-SRC-05 | The system shall allow users to sort the book list by title or by publication year. The sorting shall use a Merge Sort algorithm implemented by the team on a singly linked list. |
| FR-SRC-06 | The system shall display search results and book lists with pagination. |
| FR-SRC-07 | The system shall display the details of a book, including its cover image (if available), total copies, and available copies. |

### 1.4 Account and Reader Management

| ID | Requirement |
|---|---|
| FR-ACC-01 | The system shall allow a Guest to register a Reader account with full name, student ID, phone number, email, and password. |
| FR-ACC-02 | The system shall allow users to log in and log out. |
| FR-ACC-03 | The system shall provide a password recovery function for registered users, for example by sending a reset link or code to the registered email. |
| FR-ACC-04 | The system shall assign each Reader a unique reader ID and a library card with an issue date, an expiration date, and a status (ACTIVE or BLOCKED). |
| FR-ACC-05 | The system shall allow a Librarian to activate or block a Reader's library card. |
| FR-ACC-06 | The system shall allow a Reader to view and update their own information, such as phone number and email. |
| FR-ACC-07 | The system shall allow a Librarian to add a Reader and to search for a Reader by reader ID or name. |
| FR-ACC-08 | The system shall allow a Librarian to delete a Reader only if the Reader has no active borrowing records. |
| FR-ACC-09 | The system shall allow an Administrator to create, update, and deactivate Librarian accounts. |
| FR-ACC-10 | The system shall allow each role to use only the functions permitted to that role. |

### 1.5 Borrowing and Returning Books

| ID | Requirement |
|---|---|
| FR-BOR-01 | The system shall allow a Librarian to create a borrowing record for a Reader and one or more books. Each record shall include the reader ID, book ID, borrowing date, due date, and status. |
| FR-BOR-02 | The system shall allow borrowing only if the Reader's library card is ACTIVE and not expired. |
| FR-BOR-03 | The system shall prevent a Reader from having more than 3 books on loan at the same time (BR-01). Only books that have not been returned count toward the limit. |
| FR-BOR-04 | The system shall check that a book has at least one available copy before borrowing. If no copy is available, the system shall refuse the borrowing and let the Reader join the reservation queue of that book. |
| FR-BOR-05 | After a book is borrowed, the system shall decrease the number of available copies of that book by one. |
| FR-BOR-06 | The system shall allow a Librarian to process a return and record the actual return date. |
| FR-BOR-07 | After a book is returned, the system shall increase the number of available copies by one. |
| FR-BOR-08 | The system shall allow a Reader to view their borrowing history and the status of their loans. |
| FR-BOR-09 | The system shall identify a loan as overdue when the book has not been returned more than 14 days after the borrowing date (BR-02). |

### 1.6 Book Reservation Queue

| ID | Requirement |
|---|---|
| FR-RES-01 | When no copy of a book is available, the system shall allow a Reader to join the reservation queue of that book. |
| FR-RES-02 | The system shall keep a separate queue for each book and serve Readers in First-In, First-Out (FIFO) order. |
| FR-RES-03 | When a book is returned and its reservation queue is not empty, the system shall automatically notify the Reader at the front of the queue that the book is available. |
| FR-RES-04 | The system shall allow a Reader to cancel their reservation, and shall update the queue when a reservation is fulfilled or canceled. |

### 1.7 Reports and Statistics

| ID | Requirement |
|---|---|
| FR-REP-01 | The system shall show the 10 most borrowed books, ranked by number of borrowings. |
| FR-REP-02 | The system shall show the list of Readers who have not returned books more than 14 days after the borrowing date, including reader ID, book ID, borrowing date, and number of overdue days. |
| FR-REP-03 | The system shall show the total number of books, books currently on loan, overdue loans, and registered Readers. |
| FR-REP-04 | The system shall allow a Librarian or Administrator to view monthly statistics, including the number of borrowed books, returned books, and new Readers in a selected month. |

### 1.8 Business Rules

| ID | Business Rule |
|---|---|
| BR-01 | A Reader may have at most 3 books on loan at the same time. |
| BR-02 | A loan is overdue when the book is not returned more than 14 days after the borrowing date. |
| BR-03 | Each book has a unique book ID, and each Reader has a unique reader ID. |
| BR-04 | Reservations for the same book are served in FIFO order. |

## 2. Non-Functional Requirements

Requirements that depend on an optional feature (online reservations or fine collection) apply only if that feature is included in the approved project scope, consistent with FR-CIR-12 and FR-ADM-07.

### 2.1 Product Requirements

#### 2.1.1 Usability Requirements

| ID | Requirement |
|---|---|
| NFR-USA-01 | A library staff member who has read the user manual shall be able to perform checkout and return independently after no more than 30 minutes of orientation. |
| NFR-USA-02 | On the staff checkout and return screens, the cursor shall automatically be placed in the barcode input field when the screen loads and after each scan is confirmed, so that staff can scan items continuously without using the mouse. |
| NFR-USA-03 | The web application shall display and operate correctly on the latest two major versions of Google Chrome, Microsoft Edge, Mozilla Firefox, and Safari, on screen widths from 360 px (mobile) to 1920 px (desktop). |
| NFR-USA-04 | All system messages shall be presented in English. Each validation or error message shall state what went wrong and what the user should do next (e.g., "Card is BLOCKED. Please contact the librarian."). |

#### 2.1.2 Performance and Capacity Requirements

| ID | Requirement |
|---|---|
| NFR-PER-01 | Book search and catalog filtering shall return and display results within 1.5 seconds on a catalog of 20,000 book titles. |
| NFR-PER-02 | Barcode verification and confirmation of a single checkout or return item shall complete within 2.0 seconds. |
| NFR-PER-03 | The system shall send the password recovery email within 5.0 seconds after a valid reset request is accepted. |
| NFR-PER-04 | With 100 concurrent active users, the system shall still meet the response-time targets in NFR-PER-01 and NFR-PER-02. |
| NFR-PER-05 | The database shall support up to 50,000 BookCopy records, 20,000 BookTitle records, 10,000 Reader accounts, and 500,000 circulation transaction records without violating NFR-PER-01 and NFR-PER-02. |

#### 2.1.3 Reliability and Robustness Requirements

| ID | Requirement |
|---|---|
| NFR-REL-01 | The web application shall be available at least 99.0% of the library's service hours (07:00–21:00, Monday–Saturday). |
| NFR-REL-02 | All circulation and inventory operations that change data shall be executed as database transactions. If a crash, power failure, or network failure occurs during an operation, the incomplete operation shall be rolled back so that the database returns to its most recent consistent state. After recovery, no partially completed loan or return shall remain in the database. |

#### 2.1.4 Security Requirements

| ID | Requirement |
|---|---|
| NFR-SEC-01 | All communication between clients and the web application over the Internet shall be encrypted using HTTPS with TLS 1.2 or higher. |
| NFR-SEC-02 | User passwords shall be stored only as salted hashes using bcrypt with a work factor of at least 10. Plaintext passwords shall never be stored or written to logs. |
| NFR-SEC-03 | Password recovery links shall use random, single-use tokens that expire 15 minutes after they are issued. A token shall become invalid immediately after it is used or expires. |
| NFR-SEC-04 | The system shall accept no more than 3 password reset requests per email address within any 1-hour period. |
| NFR-SEC-05 | The role-based permissions defined in FR-ADM-06 shall be checked on the server for every request, so that a user cannot access a function outside their role even by calling the server directly. |
| NFR-SEC-06 | An authenticated session shall expire automatically after 60 minutes of inactivity. |
| NFR-SEC-07 | The system shall keep an audit log of all administrative actions (account changes, card activation or blocking, and other manual staff actions). Audit log entries shall not be editable or deletable by any user role. |

### 2.2 Organizational Requirements

| ID | Requirement |
|---|---|
| NFR-ORG-01 | The system shall be deployed as a web application accessible through the browsers listed in NFR-USA-03, both within the campus network (LAN) and over the Internet. |
| NFR-ORG-02 | The system shall be developed using a three-tier architecture consisting of a Presentation Layer, a Business Logic Layer, and a Data Access Layer. |
| NFR-ORG-03 | The system shall use an email delivery service (an SMTP server or a cloud email API) to send password recovery links to users' registered email addresses. |
| NFR-ORG-04 | The relational database shall be normalized to at least Third Normal Form (3NF). |
| NFR-ORG-05 | The database shall be backed up automatically every day at 00:00, and each daily backup shall be kept for at least 30 days. |

### 2.3 External Requirements

| ID | Requirement |
|---|---|
| NFR-EXT-01 | Reader personal data, email addresses, and borrowing histories shall be handled in accordance with Decree No. 13/2023/ND-CP on personal data protection. Personal data shall be visible only to the Reader concerned and to authorized staff. |
| NFR-EXT-02 | If online reservations are included in the approved project scope, reservations for the same book title shall be served in first-come, first-served (FIFO) order, and staff shall not be able to change the queue order manually. |
| NFR-EXT-03 | If fine collection is included in the approved project scope, every fine or compensation payment (FR-CIR-09, FR-CIR-10, FR-ADM-07) shall produce a printable receipt and an audit record that cannot be edited or deleted, to support financial auditing. |

### 2.4 Summary of Quantitative Metrics

| System Property | Measure | Target Value | Verification Method | Related Requirement |
|---|---|---|---|---|
| **Speed** | User/event response time (search) | ≤ 1.5 s on 20,000 titles | Automated query benchmark | NFR-PER-01 |
| **Speed** | Transaction processing time | ≤ 2.0 s per checkout/return item | Timer on barcode checkout/return | NFR-PER-02 |
| **Speed** | Email dispatch latency | ≤ 5.0 s | Email server dispatch log | NFR-PER-03 |
| **Speed** | Response time under load | Targets of NFR-PER-01/02 met with 100 concurrent users | Load test simulation | NFR-PER-04 |
| **Size** | Data capacity | Up to 50,000 copies, 20,000 titles, 10,000 Readers, 500,000 transactions | Load test with generated data | NFR-PER-05 |
| **Ease of use** | Training time | ≤ 30 minutes with user manual | Usability trial with sample tasks | NFR-USA-01 |
| **Reliability** | Availability | ≥ 99.0% of service hours | Server uptime monitoring log | NFR-REL-01 |
| **Robustness** | Incomplete transactions after recovery | 0 | Crash test during a checkout transaction | NFR-REL-02 |
| **Portability** | Number of target systems | 4 browsers; 360–1920 px screen widths | Cross-browser test | NFR-USA-03 |
| **Security** | Communication encryption | HTTPS / TLS 1.2+ | TLS handshake inspection | NFR-SEC-01 |
| **Security** | Password hashing | bcrypt, work factor ≥ 10 | Database hash inspection | NFR-SEC-02 |
| **Security** | Reset token validity | ≤ 15 minutes, single use | Automated token expiration test | NFR-SEC-03 |

## 3. Data Flow Diagram

*(To be updated)*

## 4. Use Case Diagram

*(To be updated)*

## 5. Class Diagram

*(To be updated)*

## 6. Data Model

*(To be updated)*

## 7. Interface Design Description

*(To be updated)*
