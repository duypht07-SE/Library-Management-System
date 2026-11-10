# Software Requirements Specification and Design Document
**Project Name:** Library Management System (LMS)

## 1. Functional Requirements

### 1.1 Overview

This section lists the functional requirements of the Library Management System (LMS), grouped by actor.

**Actors**

- **Guest**: a visitor who accesses the system without logging in.
- **Reader**: a registered member who has logged in. A Reader has all Guest functions.
- **Librarian**: library staff who manage books, borrowing, returning, and reader cards.
- **Administrator**: the user who manages staff accounts, role permissions, password resets, and system settings.
- **System**: the automatic actor that runs scheduled or event-based tasks without human action.

**Conventions**

- The word **"shall"** indicates a mandatory requirement.
- Requirement IDs use the format `FR-<ACTOR>-<NN>`.

---

### 1.2 Guest

| ID | Requirement |
|---|---|
| FR-GST-01 | A Guest shall be able to submit a registration request by providing personal information (full name, student/staff ID, email, phone number, and password). The System shall check for duplicate email addresses, phone numbers, or IDs and, if none exist, create the account with pending status. |
| FR-GST-02 | A Guest shall be able to search the public catalog by title, author, ISBN, or category and view whether a book is available or out of stock. Guests shall not be able to borrow or reserve books. |
| FR-GST-03 | A Guest shall be able to view the library's rules, opening hours, events, and news. |
| FR-GST-04 | A Guest shall be able to log in with an account and password. The System shall display the interface corresponding to the account's role (Reader, Librarian, or Administrator). If the login details are incorrect or the account is locked, the System shall display an error message. |
| FR-GST-05 | A Guest who has forgotten their password shall be able to submit a password reset request using their registered email address or ID. An Administrator shall be able to review and process the request by resetting the password. |

### 1.3 Reader

| ID | Requirement |
|---|---|
| FR-RDR-01 | A Reader shall be able to use all Guest functions, including searching for books and viewing library information. |
| FR-RDR-02 | A Reader shall be able to view and update their personal information, including their password, avatar, phone number, and contact email. |
| FR-RDR-03 | A Reader with an active card shall be able to reserve a book online when all copies are borrowed. The System shall add the Reader to a first-in, first-out (FIFO) waiting queue. A Reader shall be able to cancel their reservation. |
| FR-RDR-04 | A Reader shall be able to request renewal of a borrowed book before its due date. |
| FR-RDR-05 | The System shall approve a renewal request only if the Reader's account is active, the book is not overdue, the renewal limit has not been reached, and no other Reader has reserved the book. |
| FR-RDR-06 | A Reader shall be able to view their borrowing history, including currently borrowed books, returned books, due dates, reservation status, and recorded rule violations. |
| FR-RDR-07 | A Reader shall be able to read e-books and digital course materials online or download them in PDF or EPUB format. |

### 1.4 Librarian

| ID | Requirement |
|---|---|
| FR-LIB-01 | A Librarian shall be able to add a new book title and its physical copies, each with a unique barcode, to the catalog. |
| FR-LIB-02 | A Librarian shall be able to edit book information and update copy details. |
| FR-LIB-03 | A Librarian shall be able to classify a book by standard code (DDC/ISBN) and category. |
| FR-LIB-04 | A Librarian shall be able to set and update the shelf location of each physical copy. |
| FR-LIB-05 | A Librarian shall be able to retire an old, torn, or outdated book copy by changing its status to canceled. The System shall prevent a copy that is currently on loan from being retired. |
| FR-LIB-06 | A Librarian shall be able to create a borrowing record at the counter by scanning the Reader's card code and each book copy's barcode. |
| FR-LIB-07 | Before saving a borrowing record, the System shall verify that the Reader's card is active, the Reader has no overdue books, the maximum borrowing limit has not been reached, and the book copy is available or reserved for that Reader. |
| FR-LIB-08 | A Librarian shall be able to record a returned book by scanning its barcode. The System shall save the return date and set the copy status to available, or to on hold if another Reader is waiting in the reservation queue. |
| FR-LIB-09 | A Librarian shall be able to record the condition of a returned book (intact, damaged, or lost). The System shall log a violation on the Reader's account if the book is returned late, damaged, or lost. |
| FR-LIB-10 | A Librarian shall be able to review new library card registrations and approve or reject them. |
| FR-LIB-11 | A Librarian shall be able to lock a Reader's account when the Reader breaks library rules (such as keeping overdue books or damaging or losing a book), and unlock the account after the issue is resolved at the counter. |
| FR-LIB-12 | A Librarian shall be able to run batch barcode scans to compare the actual number of books on the shelves with the number recorded in the catalog. |

### 1.5 Administrator

| ID | Requirement |
|---|---|
| FR-ADM-01 | An Administrator shall be able to create Librarian accounts, edit their information, and lock or unlock them. |
| FR-ADM-02 | An Administrator shall be able to create roles and assign specific permissions to each role (for example, one Librarian role may handle borrowing, returning, and reader cards, while another may manage only the book catalog). |
| FR-ADM-03 | An Administrator shall be able to review password reset requests and manually reset the password of any Reader or Librarian account to a temporary password. |
| FR-ADM-04 | An Administrator shall be able to configure library rules, including the maximum number of books a Reader may borrow, the maximum loan period, the maximum number of renewals per loan, and the number of days a reserved book is held on the waiting shelf. |
| FR-ADM-05 | An Administrator shall be able to view and export monthly or yearly charts and reports on borrowing counts, overdue loans, book stock, and new Readers. |
| FR-ADM-06 | An Administrator shall be able to back up the database. |
| FR-ADM-07 | An Administrator shall be able to restore the database from a backup when a technical failure occurs. |
| FR-ADM-08 | An Administrator shall be able to view audit logs of user logins, role and permission changes, password resets, and data edits. |

### 1.6 System (Automatic Functions)

| ID | Requirement |
|---|---|
| FR-SYS-01 | The system shall scan all active borrowing records every day at 00:00, mark unreturned loans past their due date as overdue, and block the Reader from borrowing or renewing books until the overdue books are returned. |
| FR-SYS-02 | The system shall send in-app notifications to Readers when a borrowed book is due in 2 days, when a book is overdue, or when a reserved book is ready for pickup at the counter. |
| FR-SYS-03 | The system shall cancel a reservation hold if the Reader does not pick up the book within the allowed hold days (for example 3 days), and shall set the book copy back to available or assign it to the next Reader in the waiting queue. |
| FR-SYS-04 | The system shall check user role permissions on every action and log the actions of Librarians and Administrators (such as book edits, account locks, role changes, and password resets) for security tracking. |


## 2. Non-Functional Requirements

### 2.1 Overview

This section describes the quality requirements of the Library Management System (LMS): how well the system shall perform, not what functions it provides. Each requirement is written to be measurable where possible.

**Conventions**

- The word **"shall"** indicates a mandatory requirement.
- Requirement IDs use the format `NFR-<CATEGORY>-<NN>`.
- The numeric values (response times, number of users, and so on) are **proposed targets**. The team shall confirm them with the instructor before treating them as final.
- The "Related FR" column links a requirement to the functional requirements in Section 1.

---

### 2.2 Performance

| ID | Requirement | Related FR |
|---|---|---|
| NFR-PER-01 | A Guest or Reader shall receive book search results within 2 seconds for a catalog of up to 100,000 book records. | FR-GST-02, FR-RDR-01 |
| NFR-PER-02 | A Librarian shall receive confirmation that a borrowing or returning record has been saved within 2 seconds after scanning the barcode. | FR-LIB-06, FR-LIB-08 |
| NFR-PER-03 | An Administrator shall be able to load standard pages within 3 seconds and generate statistical reports within 5 seconds. | FR-ADM-05 |
| NFR-PER-04 | The LMS shall support at least 100 concurrent active users while keeping response times within 10% of the baseline response times measured with one active user. | All |
| NFR-PER-05 | The daily overdue-loan and expired-reservation-hold processing task shall finish within 10 minutes for up to 50,000 active records. | FR-SYS-01, FR-SYS-03 |

### 2.3 Security

| ID | Requirement | Related FR |
|---|---|---|
| NFR-SEC-01 | The authentication service shall hash all user passwords using bcrypt (cost factor 12 or higher) before saving them to the database. No component shall store plain-text passwords or include them in logs. | FR-GST-01, FR-GST-04, FR-RDR-02, FR-ADM-03 |
| NFR-SEC-02 | All client-server connections to the LMS shall use HTTPS with TLS 1.2 or TLS 1.3. | All |
| NFR-SEC-03 | The LMS server shall check Role-Based Access Control (RBAC) permissions for every request and allow users to perform only actions permitted for their assigned roles. | FR-GST-04, FR-ADM-02, FR-SYS-04 |
| NFR-SEC-04 | A Reader shall only be able to view and edit their own profile, borrowing history, and reservation records. | FR-RDR-02, FR-RDR-06 |
| NFR-SEC-05 | When an Administrator resets a forgotten password, the temporary password shall expire after 24 hours and the user shall be required to set a new password upon logging in. | FR-GST-05, FR-ADM-03 |
| NFR-SEC-06 | The LMS shall end inactive sessions after 30 minutes and lock an account for 15 minutes after 5 consecutive failed login attempts. | FR-GST-04 |
| NFR-SEC-07 | Audit logs shall be append-only; no user, including an Administrator, shall be able to edit or delete existing log entries through the application. | FR-ADM-08, FR-SYS-04 |

### 2.4 Reliability and Data Integrity

| ID | Requirement | Related FR |
|---|---|---|
| NFR-REL-01 | The LMS shall maintain at least 99.5% uptime during library opening hours. | All |
| NFR-REL-02 | Borrowing, returning, and reservation updates shall run as atomic database transactions. If an error occurs midway, the database shall roll back all changes from that transaction. | FR-RDR-03, FR-LIB-06, FR-LIB-07, FR-LIB-08 |
| NFR-REL-03 | The database shall use row-level locking when checking out or reserving a book copy so two users cannot borrow or reserve the last available copy at the same time. | FR-RDR-03, FR-LIB-06, FR-LIB-07 |
| NFR-REL-04 | A full database restore from a backup file shall complete within 30 minutes. | FR-ADM-06, FR-ADM-07 |

### 2.5 Usability

| ID | Requirement | Related FR |
|---|---|---|
| NFR-USA-01 | The web interface shall support UTF-8 encoding and display properly on desktop and mobile screens from 360px to 1920px wide. | All |
| NFR-USA-02 | At the circulation desk, the cursor shall automatically move to the next barcode field after each scan so the Librarian can check out books without using the mouse. | FR-LIB-06, FR-LIB-08 |
| NFR-USA-03 | Error messages (such as wrong password, locked card, or borrowing limit reached) shall state the specific reason for the failure. | FR-GST-04, FR-LIB-07 |

### 2.6 Compatibility

| ID | Requirement | Related FR |
|---|---|---|
| NFR-COM-01 | The web application shall run on the latest two versions of Google Chrome, Mozilla Firefox, Microsoft Edge, and Safari. | All |
| NFR-COM-02 | The LMS client shall accept input from standard USB and Bluetooth barcode scanners operating in keyboard wedge (HID) mode. | FR-LIB-01, FR-LIB-06, FR-LIB-08, FR-LIB-12 |

### 2.7 Maintainability

| ID | Requirement | Related FR |
|---|---|---|
| NFR-MNT-01 | The codebase shall separate the user interface, business logic, and data access into distinct layers (such as MVC). | All |
| NFR-MNT-02 | Library rules (borrowing limits, loan days, renewal limits, and hold days) shall be stored in database configuration tables rather than hard-coded in the source code. | FR-ADM-04 |

### 2.8 Development Requirements

| ID | Requirement | Related FR |
|---|---|---|
| NFR-DEV-01 | The core business logic and object-oriented classes shall be written in C++ (C++17 standard) or Python 3.11+, following the class structure and inheritance hierarchy defined in the Class Diagram. | All |
| NFR-DEV-02 | The user interface shall be built using HTML5, CSS3, and JavaScript (with Python Flask/Django) or Qt Framework for desktop screens to match the designed UI mockups. | All |
| NFR-DEV-03 | The system shall use MySQL 8.0 (or SQLite 3) as the relational database management system (RDBMS) to store tables, enforce foreign keys, and run ACID transactions. | All |
| NFR-DEV-04 | The team shall use Git and GitHub to manage source code, track issues, and store project documents. | All |
| NFR-DEV-05 | System diagrams (DFD, Use Case, Class Diagram, and ERD) shall be drawn with draw.io, and interface screens shall be designed with Figma. | All |


## 3. Data Flow Diagram (DFD)

### 3.1 Scope

The DFDs cover account management, book management, borrowing and returning, fines, and library rules and reports. The following requirements from Section 1 are left out of the diagrams:

| Requirement | Reason |
|---|---|
| FR-GST-03 (library information, news, events) | Static content with no data processing |
| FR-RDR-08 (online fine payment), FR-RDR-09 (e-books) | Optional in Section 1 ("if the system integrates...") |
| FR-LIB-13 (inventory audit) | Periodic task outside the daily workflow |
| FR-ADM-02, FR-ADM-05 to FR-ADM-07 (permissions, backup, restore, audit logs) | System maintenance |
| FR-SYS-04 (automatic action logging) | Internal behavior with no user-visible data flow |

FR-SYS-01 to FR-SYS-03 (overdue fines, reminders, expired holds) are handled inside processes 3.0 and 4.0.

### 3.2 Context Diagram (Level 0 DFD)

The whole system is drawn as one process, `0 Library Management System`, connected to four external entities.

![Context Diagram (Level 0 DFD)](../diagrams/dfd-level-0.png)

#### External Entities

| Entity | Description |
|---|---|
| Guest | Visitor who has not logged in. Registers, logs in, and searches books. |
| Reader | Library member. Reserves and renews books, views loans and fines. |
| Librarian | Staff member. Manages books and reader cards, handles borrowing, returning, and fines at the counter. |
| Administrator | Manages Librarian accounts, library rules, and reports. |

#### Data Flows

| No. | From | To | Data | Related FR |
|---|---|---|---|---|
| 1 | Guest | LMS | Registration Info, Login Info, Search Request | FR-GST-01, FR-GST-02, FR-GST-04 |
| 2 | LMS | Guest | Search Results, Login Result | FR-GST-02, FR-GST-04 |
| 3 | Reader | LMS | Profile Update, Reservation / Renewal Request | FR-RDR-02, FR-RDR-03, FR-RDR-04 |
| 4 | LMS | Reader | Loan History, Fine Status, Reminders | FR-RDR-06, FR-RDR-07, FR-SYS-02 |
| 5 | Librarian | LMS | Book Data, Borrow / Return, Fine Payment, Card Approval / Lock | FR-LIB-01 to FR-LIB-07, FR-LIB-09 to FR-LIB-12 |
| 6 | LMS | Librarian | Loan Receipt | FR-LIB-06, FR-LIB-07 |
| 7 | Administrator | LMS | Librarian Account, Library Rules | FR-ADM-01, FR-ADM-03 |
| 8 | LMS | Administrator | Reports | FR-ADM-04 |

### 3.3 Data Stores

| Store | Name | Content |
|---|---|---|
| D1 | Accounts | User accounts, roles, library cards, card status |
| D2 | Books | Book titles, physical copies, copy status |
| D3 | Loans & Reservations | Borrowing records, due dates, renewals, reservation queues |
| D4 | Fines | Violations, fine amounts, payment status |

### 3.4 Level 1 DFD

Process 0 is split into five processes. Each process uses the data store drawn below it.

![Level 1 DFD](../diagrams/dfd-level-1.png)

#### Process Descriptions

| Process | Inputs | Outputs | Data Stores | Related FR |
|---|---|---|---|---|
| 1.0 Manage Accounts | Registration Info, Login Info (Guest); Profile Update (Reader); Card Approval / Lock (Librarian); Librarian Account (Administrator) | Login Result (Guest) | D1 read/write | FR-GST-01, FR-GST-04, FR-RDR-02, FR-LIB-11, FR-LIB-12, FR-ADM-01 |
| 2.0 Manage Books | Search Request (Guest); Book Data (Librarian) | Search Results (Guest) | D2 read/write | FR-GST-02, FR-LIB-01 to FR-LIB-05 |
| 3.0 Borrow & Return | Reservation / Renewal Request (Reader); Borrow / Return (Librarian); Loan Rules (from 5.0) | Loan History, Reminders (Reader); Loan Receipt (Librarian); Overdue Info (to 4.0) | D3 read/write; D2 write (Copy Status) | FR-RDR-03 to FR-RDR-06, FR-LIB-06, FR-LIB-07, FR-SYS-02, FR-SYS-03 |
| 4.0 Manage Fines | Overdue Info (from 3.0); Fine Payment (Librarian) | Fine Status (Reader) | D4 read/write | FR-RDR-07, FR-LIB-09, FR-LIB-10, FR-SYS-01 |
| 5.0 Manage Rules & Reports | Library Rules (Administrator); Loan Data (D3); Fine Data (D4) | Reports (Administrator); Loan Rules (to 3.0) | D3, D4 read | FR-ADM-03, FR-ADM-04 |

#### Balancing with Level 0

The flows between external entities and the system in Level 1 have the same names as in Level 0. Level 1 adds no new external flows. Account Data, Book Data, Loan Data, Copy Status, Fine Data, Overdue Info, and Loan Rules are internal flows.

#### Related Non-Functional Requirements

| Process | NFR | Constraint |
|---|---|---|
| 1.0 | NFR-SEC-01, NFR-SEC-05, NFR-SEC-06 | Passwords are hashed. Sessions end after 30 minutes of inactivity. An account is locked for 15 minutes after 5 failed logins. |
| 1.0 | NFR-SEC-03, NFR-SEC-04 | Access is role-based. A Reader can see only their own data. |
| 2.0 | NFR-PER-01 | Search results within 2 seconds. |
| 3.0 | NFR-PER-02, NFR-REL-02, NFR-REL-03 | A borrow or return is saved within 2 seconds after the scan. A failed transaction is rolled back. One copy cannot be lent to two Readers at once. |
| 3.0 | NFR-PER-04, NFR-REL-06 | The daily overdue scan finishes within 30 minutes. Reminders are sent asynchronously. |
| All | NFR-SEC-07, NFR-USA-01, NFR-COM-03 | Input is validated. The interface is in English (UTF-8), dates use DD/MM/YYYY, currency is VND. |

## 4. Use Case Diagram

### 4.1 Overview

The diagram covers the same functions as the DFDs in Section 3.

![Use Case Diagram](../diagrams/use-case.png)

### 4.2 Actors

| Actor | Description |
|---|---|
| User | Parent actor for every account holder. Linked to Log In. |
| Guest | Visitor who has not logged in. Registers, logs in, and searches books (FR-GST-01, FR-GST-02, FR-GST-04). |
| Reader | Child of User. Library member (FR-RDR-01). |
| Librarian | Child of User. Library staff. |
| Administrator | Child of User. Manages staff accounts and library rules. |

Reader, Librarian, and Administrator get Log In from User through actor generalization, so the diagram does not link them to Log In one by one. After a Guest logs in, the system gives the user the Reader, Librarian, or Administrator role of that account (FR-GST-04).

### 4.3 Use Cases

| Actor | Use Case | Related FR |
|---|---|---|
| Guest | Register Account | FR-GST-01 |
| Guest, Reader | Search Books | FR-GST-02 |
| Guest, User | Log In | FR-GST-04 |
| Reader | Update Profile | FR-RDR-02 |
| Reader | Reserve Book | FR-RDR-03 |
| Reader | Renew Loan | FR-RDR-04, FR-RDR-05 |
| Reader | View Borrowing History | FR-RDR-06 |
| Reader | View Fines | FR-RDR-07 |
| Librarian | Manage Books | FR-LIB-01 to FR-LIB-05 |
| Librarian | Approve / Lock Reader Card | FR-LIB-11, FR-LIB-12 |
| Librarian | Check Out Books | FR-LIB-06 |
| Librarian | Check In Books | FR-LIB-07, FR-LIB-08 |
| Librarian | Record Violation | FR-LIB-09 |
| Librarian | Record Fine Payment | FR-LIB-10 |
| Administrator | Manage Librarian Accounts | FR-ADM-01 |
| Administrator | Configure Library Rules | FR-ADM-03 |
| Administrator | View Reports | FR-ADM-04 |

### 4.4 Relationships

| From | To | Type | Meaning |
|---|---|---|---|
| Reader, Librarian, Administrator | User | Generalization | The three roles inherit Log In from User. |
| Record Violation | Check In Books | `<<extend>>` | Runs only when the returned book is late, damaged, or lost (FR-LIB-09). |
| Actor | Use Case | Association | The actor performs the use case. |

### 4.5 Related Non-Functional Requirements

| Use Case | NFR | Constraint |
|---|---|---|
| Log In | NFR-SEC-01, NFR-SEC-05, NFR-SEC-06 | Hashed passwords, 30-minute session timeout, 15-minute lock after 5 failed attempts |
| Search Books | NFR-PER-01 | Results within 2 seconds |
| View Borrowing History, View Fines | NFR-SEC-04 | A Reader sees only their own data |
| Check Out Books, Check In Books | NFR-PER-02, NFR-REL-02, NFR-REL-03 | Saved within 2 seconds after the scan; rollback on failure; no double loan of one copy |
| All | NFR-SEC-03 | Each role can use only its own use cases |

## 5. Class Diagram

### 5.1 Overview

This section lists the main classes of the Library Management System (LMS) along with their attributes, methods, and relationships.

![Class Diagram](../diagrams/Class-Diagram.drawio.png)

### 5.2 Class Descriptions

| Class | Description | DFD Store | Related FR |
|---|---|---|---|
| `User` | Base class for all accounts (`userId`, `fullName`, `email`, `phone`, `passwordHash`, `status`, `failedLogins`, `lockedUntil`) with login, logout, and profile update methods. | D1 | FR-GST-01, FR-GST-04, FR-RDR-02 |
| `Reader` | Inherits from `User`. Adds `cardCode` and methods for reserving books, requesting renewals, and viewing borrowing history and fines. | D1 | FR-RDR-01 to FR-RDR-07 |
| `Librarian` | Inherits from `User`. Provides methods to manage books, approve or lock reader cards, check out and check in books, and record fines and payments. | D1 | FR-LIB-01 to FR-LIB-12 |
| `Administrator` | Inherits from `User`. Provides methods to manage librarian accounts, configure library rules, and view reports. | D1 | FR-ADM-01, FR-ADM-03, FR-ADM-04 |
| `Book` | Contains book information (`bookId`, `isbn`, `ddcCode`, `title`, `author`, `category`, `availableCopies`) and search method. | D2 | FR-GST-02, FR-LIB-01 to FR-LIB-03 |
| `BookCopy` | A physical copy of a book on the shelf (`copyId`, `barcode`, `shelfLocation`, `status`, `condition`). | D2 | FR-LIB-04, FR-LIB-05, FR-LIB-08 |
| `BorrowRecord` | Records a borrowing transaction (`borrowId`, `borrowDate`, `dueDate`, `returnDate`, `returnCondition`, `renewCount`, `status`). | D3 | FR-RDR-04 to FR-RDR-06, FR-LIB-06 to FR-LIB-08 |
| `Reservation` | Keeps track of online book holds and waiting queues (`reservationId`, `reserveDate`, `expireDate`, `status`). | D3 | FR-RDR-03, FR-SYS-03 |
| `Notification` | Stores reminder messages (`notificationId`, `channel`, `message`, `status`, `sentAt`) sent to Readers. | D3 | FR-SYS-02 |
| `Fine` | Records a reader violation and its payment status (`fineId`, `reason`, `amount`, `isPaid`, `paidAt`). | D4 | FR-RDR-07, FR-LIB-09, FR-LIB-10, FR-SYS-01 |
| `SystemConfig` | Stores library settings (`configKey`, `configValue`, `updatedAt`) such as borrowing limits and daily fine rates. | Internal | FR-ADM-03 |


## 6. Data Model

### 6.1 Overview

The database uses UTF-8 (`utf8mb4`) encoding (`NFR-USA-01`, `NFR-COM-03`) and consists of 8 relational tables in Third Normal Form (3NF). The tables match the classes in Section 5 and the four data stores (`D1` to `D4`) in Section 3.3. The inheritance hierarchy of `User` (`Reader`, `Librarian`, `Administrator`) is mapped into a single `users` table using a `role` column.

### 6.2 Entity-Relationship Diagram (ERD)

![Entity-Relationship Diagram](../diagrams/erd.png)

### 6.3 Mapping to DFD Data Stores

| DFD Store | Store Name | Mapped Database Tables |
|---|---|---|
| **D1** | Accounts | `users` |
| **D2** | Books | `books`, `book_copies` |
| **D3** | Loans & Reservations | `borrow_records`, `reservations`, `notifications` |
| **D4** | Fines | `fines` |
| **Internal** | Process 5.0 Rules | `system_configs` |

### 6.4 Data Dictionary (Table Specifications)

#### 1. `users` (Store D1)
Stores accounts for Readers, Librarians, and Administrators (`FR-GST-01`, `FR-GST-04`, `FR-RDR-02`, `FR-LIB-11`, `FR-LIB-12`, `FR-ADM-01`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `user_id` | INT | PK, AUTO_INCREMENT | Unique user identifier |
| `role` | VARCHAR(20) | NOT NULL | Account role: `READER`, `LIBRARIAN`, `ADMIN` |
| `card_code` | VARCHAR(30) | UNIQUE, NULL | Library card barcode (for Readers only) |
| `full_name` | VARCHAR(100) | NOT NULL | Full name of the user |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | Unique email address |
| `phone` | VARCHAR(15) | UNIQUE, NOT NULL | Unique phone number |
| `password_hash` | VARCHAR(255) | NOT NULL | Salted Bcrypt password hash (`NFR-SEC-01`) |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | Account status: `PENDING`, `ACTIVE`, `LOCKED` |
| `failed_logins` | INT | NOT NULL, DEFAULT 0 | Consecutive failed login attempts (`NFR-SEC-06`) |
| `locked_until` | DATETIME | NULL | End time of temporary login lock (`NFR-SEC-06`) |

#### 2. `books` (Store D2)
Stores book title metadata (`FR-GST-02`, `FR-LIB-01` to `FR-LIB-03`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `book_id` | INT | PK, AUTO_INCREMENT | Unique book identifier |
| `isbn` | VARCHAR(20) | UNIQUE, NOT NULL | Standard ISBN code |
| `ddc_code` | VARCHAR(20) | NOT NULL | Dewey Decimal Classification code |
| `title` | VARCHAR(255) | NOT NULL | Book title |
| `author` | VARCHAR(150) | NOT NULL | Author name |
| `category` | VARCHAR(100) | NOT NULL | Book category |
| `available_copies` | INT | NOT NULL, DEFAULT 0 | Number of copies currently available on the shelf |

#### 3. `book_copies` (Store D2)
Stores physical book copies for barcode scanning (`FR-LIB-04`, `FR-LIB-05`, `FR-LIB-08`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `copy_id` | INT | PK, AUTO_INCREMENT | Unique physical copy identifier |
| `book_id` | INT | FK (`books.book_id`), NOT NULL | Reference to the book title |
| `barcode` | VARCHAR(50) | UNIQUE, NOT NULL | Barcode label on the physical copy |
| `shelf_location` | VARCHAR(50) | NOT NULL | Shelf location in the storage |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'AVAILABLE' | `AVAILABLE`, `BORROWED`, `RESERVED`, `CANCELED` |
| `condition` | VARCHAR(20) | NOT NULL, DEFAULT 'INTACT' | Physical state: `INTACT`, `DAMAGED`, `LOST` |

#### 4. `borrow_records` (Store D3)
Stores counter borrowing, returning, and loan renewal records (`FR-RDR-04` to `FR-RDR-06`, `FR-LIB-06` to `FR-LIB-08`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `borrow_id` | INT | PK, AUTO_INCREMENT | Unique borrowing transaction identifier |
| `reader_id` | INT | FK (`users.user_id`), NOT NULL | Reader who borrowed the book |
| `copy_id` | INT | FK (`book_copies.copy_id`), NOT NULL | Borrowed physical book copy |
| `librarian_id` | INT | FK (`users.user_id`), NOT NULL | Librarian who created the transaction |
| `borrow_date` | DATETIME | NOT NULL | Date and time of checkout |
| `due_date` | DATETIME | NOT NULL | Expected return due date |
| `return_date` | DATETIME | NULL | Actual return date (`NULL` if not yet returned) |
| `return_condition` | VARCHAR(20) | NULL | Recorded condition upon return (`INTACT`, `DAMAGED`, `LOST`) |
| `renew_count` | INT | NOT NULL, DEFAULT 0 | Number of times the loan has been renewed |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'BORROWED' | `BORROWED`, `RETURNED`, `OVERDUE` |

#### 5. `reservations` (Store D3)
Stores online book reservations and waiting queues (`FR-RDR-03`, `FR-SYS-03`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `reservation_id` | INT | PK, AUTO_INCREMENT | Unique reservation identifier |
| `reader_id` | INT | FK (`users.user_id`), NOT NULL | Reader who placed the reservation |
| `book_id` | INT | FK (`books.book_id`), NOT NULL | Reserved book title |
| `copy_id` | INT | FK (`book_copies.copy_id`), NULL | Specific copy held on the waiting shelf when returned |
| `reserve_date` | DATETIME | NOT NULL | Date and time the reservation was made |
| `expire_date` | DATETIME | NULL | Pickup deadline before automatic cancellation |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'WAITING' | `WAITING`, `READY`, `COMPLETED`, `CANCELED` |

#### 6. `fines` (Store D4)
Stores violation records and counter fine payments (`FR-RDR-07`, `FR-LIB-09`, `FR-LIB-10`, `FR-SYS-01`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `fine_id` | INT | PK, AUTO_INCREMENT | Unique fine identifier |
| `borrow_id` | INT | FK (`borrow_records.borrow_id`), NOT NULL | Related borrowing record |
| `reason` | VARCHAR(50) | NOT NULL | Violation reason: `LATE_RETURN`, `DAMAGED`, `LOST` |
| `amount` | DECIMAL(10,2) | NOT NULL | Fine amount in VND (`NFR-COM-03`) |
| `is_paid` | BOOLEAN | NOT NULL, DEFAULT FALSE | Payment status (`TRUE` if paid, `FALSE` if unpaid) |
| `paid_at` | DATETIME | NULL | Date and time when the fine was paid at the counter |

#### 7. `system_configs` (Process 5.0 Rules)
Stores library parameters configured by the Administrator (`FR-ADM-03`, `NFR-MNT-02`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `config_key` | VARCHAR(50) | PK | Rule key: `MAX_BOOKS`, `MAX_DAYS`, `DAILY_FINE`, `HOLD_DAYS` |
| `config_value` | VARCHAR(100) | NOT NULL | Configured parameter value |
| `updated_by` | INT | FK (`users.user_id`), NOT NULL | Administrator who last updated the rule |
| `updated_at` | DATETIME | NOT NULL | Timestamp of the last update |

#### 8. `notifications` (Store D3 Reminders)
Stores automated due, overdue, and pickup reminders sent to Readers (`FR-SYS-02`, `NFR-REL-06`).

| Column Name | Data Type | Constraints & Keys | Description |
|---|---|---|---|
| `notification_id` | INT | PK, AUTO_INCREMENT | Unique notification identifier |
| `reader_id` | INT | FK (`users.user_id`), NOT NULL | Recipient Reader |
| `channel` | VARCHAR(20) | NOT NULL | Delivery channel: `EMAIL`, `SMS`, `IN_APP` |
| `message` | TEXT | NOT NULL | Reminder message content |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | Delivery status: `PENDING`, `SENT`, `FAILED` |
| `sent_at` | DATETIME | NULL | Timestamp when the notification was sent |

## 7. Interface Design Description

### 7.1 Guest

#### 7.1.1 Home
This interface shows the book categories, library news, and new books (FR-GST-03).

![Home](../ui/home.png)

#### 7.1.2 Search Books
This interface shows the books that match a keyword or category and whether each book is available (FR-GST-02).

![Search Books](../ui/searchbooks.png)

#### 7.1.3 Loading
This interface is shown while search results are loading.

![Loading](../ui/loading.png)

#### 7.1.4 Library Policies
This interface shows the library rules on membership, borrowing, reservations, and fines (FR-GST-03).

![Library Policies](../ui/librarypolicies.png)

#### 7.1.5 Help
This interface explains how to borrow a book and answers common questions (FR-GST-03).

![Help](../ui/help.png)

#### 7.1.6 Page Not Found
This interface is shown when a page does not exist.

![Page Not Found](../ui/pagenotfound.png)

#### 7.1.7 Sign In
This interface allows users to log in with email and password (FR-GST-04).

![Sign In](../ui/signin.png)

#### 7.1.8 Create Account
This interface allows Guests to register for a library card (FR-GST-01).

![Create Account](../ui/register.png)

### 7.2 Reader

#### 7.2.1 My Books
This interface allows Readers to view current loans, renew books, and view fines (FR-RDR-04 to FR-RDR-07).

![My Books](../ui/mybooks.png)

### 7.3 Librarian

#### 7.3.1 Check Out
This interface allows Librarians to lend books by scanning the reader card and book barcodes (FR-LIB-06).

![Check Out](../ui/checkout.png)

#### 7.3.2 Check In
This interface allows Librarians to record returned books, their condition, and fines (FR-LIB-07 to FR-LIB-09).

![Check In](../ui/checkin.png)

#### 7.3.3 Books
This interface allows Librarians to add, edit, and retire books (FR-LIB-01 to FR-LIB-05).

![Books](../ui/books.png)

#### 7.3.4 Readers
This interface allows Librarians to approve, lock, or unlock reader cards and record fine payments (FR-LIB-10 to FR-LIB-12).

![Readers](../ui/readers.png)

### 7.4 Administrator

#### 7.4.1 Librarian Accounts
This interface allows Administrators to add, edit, and lock librarian accounts (FR-ADM-01).

![Librarian Accounts](../ui/librarianaccounts.png)

#### 7.4.2 Rules and Reports
This interface allows Administrators to configure library rules and view reports (FR-ADM-03, FR-ADM-04).

![Rules and Reports](../ui/rulesandreports.png)

