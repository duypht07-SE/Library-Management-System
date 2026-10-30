# Software Requirements Specification and Design Document
**Project Name:** Library Management System (LMS)

## 1. Functional Requirements

### 1.1 Overview

This section lists the functional requirements of the Library Management System (LMS), grouped by actor.

**Actors**

- **Guest**: a visitor who accesses the system but has not logged in.
- **Reader**: a member who already has an account and has logged in successfully. A Reader inherits all Guest functions.
- **Librarian**: library staff responsible for physical and digital library operations.
- **Administrator**: the user with the highest authority, responsible for configuring and managing the whole system.
- **System**: the automatic actor that performs programmed tasks on a schedule or on an event, without direct human action.

**Conventions**

- The word **"shall"** indicates a mandatory requirement.
- Requirement IDs use the format `FR-<ACTOR>-<NN>`.

---

### 1.2 Guest

| ID | Requirement |
|---|---|
| FR-GST-01 | The system shall allow a Guest to register an account, or to request a library card, by entering personal information (full name, email, phone number, etc.). The system shall validate input data and check for duplicate email, phone number, or ID before creating the account. |
| FR-GST-02 | The system shall allow a Guest to search public books by title, author, or category and to see whether a book is still available or out of stock. A Guest shall not be able to borrow or reserve a book. |
| FR-GST-03 | The system shall allow a Guest to view the library's regulations, opening hours, events, and latest news. |
| FR-GST-04 | The system shall allow a Guest to log in by entering an account and a password, and shall then give the user the role of Reader, Librarian, or Administrator according to the account. If the credentials are invalid or the account is locked, the system shall display an appropriate error message. |

### 1.3 Reader

| ID | Requirement |
|---|---|
| FR-RDR-01 | The system shall give a Reader all functions of a Guest (searching books and viewing library information). |
| FR-RDR-02 | The system shall allow a Reader to view and update personal information, including changing the password, updating the avatar, and changing the phone number or contact email. |
| FR-RDR-03 | The system shall allow a Reader to reserve a book online, whether the book is on the shelf or currently borrowed by another Reader. |
| FR-RDR-04 | The system shall allow a Reader to send a renewal request, asking for more borrowing time, for books that are close to their due date. |
| FR-RDR-05 | The system shall approve a renewal request only if the book is not overdue, the borrowing limit has not been exceeded, and the book has not been reserved by another Reader. |
| FR-RDR-06 | The system shall allow a Reader to view their borrowing history, including the books currently borrowed, the books returned, the return due dates, and the status of their reservations. |
| FR-RDR-07 | The system shall allow a Reader to view the details of fines caused by late returns or damaged books. |
| FR-RDR-08 | If the system integrates a bank or e-wallet payment gateway, the system shall allow a Reader to pay fines online. |
| FR-RDR-09 | The system shall allow a Reader to read e-books and digital course materials online, or to download them in PDF or EPUB format. |

### 1.4 Librarian

| ID | Requirement |
|---|---|
| FR-LIB-01 | The system shall allow a Librarian to add a new book to the system. |
| FR-LIB-02 | The system shall allow a Librarian to edit book information. |
| FR-LIB-03 | The system shall allow a Librarian to classify a book by standard code (DDC/ISBN). |
| FR-LIB-04 | The system shall allow a Librarian to choose the shelf location of a book in the storage. |
| FR-LIB-05 | The system shall allow a Librarian to retire a book by updating its status to canceled, removing old, torn, or outdated books from the circulation catalog. |
| FR-LIB-06 | The system shall allow a Librarian to create a borrowing record at the counter by scanning the Reader's card code and the barcode on each book. |
| FR-LIB-07 | The system shall allow a Librarian to record a returned book by scanning its barcode, updating its status to available in stock, or to reserved if there is an active reservation. |
| FR-LIB-08 | The system shall allow a Librarian to check and record the condition of a returned book (whether it is intact). |
| FR-LIB-09 | The system shall allow a Librarian to create a violation record with a fine when a Reader loses or tears a book, or returns a book late. |
| FR-LIB-10 | The system shall allow a Librarian to record that a fine has been paid when the Reader pays at the counter. |
| FR-LIB-11 | The system shall allow a Librarian to review and approve registrations for new library cards. |
| FR-LIB-12 | The system shall allow a Librarian to lock or unlock a Reader's account according to the Reader's violations of library regulations. |
| FR-LIB-13 | The system shall allow a Librarian to perform periodic batch barcode scanning to compare the actual number of books on the shelves with the data shown in the software. |

### 1.5 Administrator

| ID | Requirement |
|---|---|
| FR-ADM-01 | The system shall allow an Administrator to add new Librarian accounts, edit their information, or lock them. |
| FR-ADM-02 | The system shall allow an Administrator to define roles and assign specific permissions to them (for example, one Librarian may manage only borrowing and returning, while another manages only the book storage). |
| FR-ADM-03 | The system shall allow an Administrator to configure library parameters: the maximum number of books a Reader may borrow, the maximum number of borrowing days, and the fine amount per day of late return. |
| FR-ADM-04 | The system shall allow an Administrator to view and export charts and reports on borrowing frequency, the total number of new Readers, and the total fines collected, by month or by year. |
| FR-ADM-05 | The system shall allow an Administrator to back up the database. |
| FR-ADM-06 | The system shall allow an Administrator to restore the system from a backup when a technical failure occurs. |
| FR-ADM-07 | The system shall allow an Administrator to view system audit logs (recording user login history, critical data modifications, and configuration changes) for security and auditing purposes. |

### 1.6 System (Automatic Functions)

| ID | Requirement |
|---|---|
| FR-SYS-01 | The system shall scan all borrowing records periodically every day (for example at 00:00) and, for each overdue record, automatically add the fine to the Reader's account. |
| FR-SYS-02 | The system shall automatically send reminders to Readers by email, SMS, or in-app notification when a book is due soon (2 days before the due date), when a book is overdue, or when a reserved book is available on the shelf for pickup. |
| FR-SYS-03 | The system shall automatically cancel a reservation hold if the Reader does not pick up the book within X days (for example 3 days) after the book is placed on the waiting shelf, and shall return the book to the available state or assign it to the next Reader in the reservation queue. |
| FR-SYS-04 | The system shall automatically log the actions of Librarians and Administrators (for example who edited a book or who deleted an account) for security and error-tracing purposes. |


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
| NFR-PER-01 | The system shall return book search results within 2.0 seconds under normal load for a database containing up to 100,000 book records. | FR-GST-02 |
| NFR-PER-02 | The system shall save a borrowing or returning transaction and show the result to the Librarian within 2.0 seconds after the barcode is scanned. | FR-LIB-06, FR-LIB-07 |
| NFR-PER-03 | The system shall support at least 100 concurrent active users without more than 10% degradation in average response time. | All |
| NFR-PER-04 | The daily scan of borrowing records (fine calculation and notification dispatch) shall complete within 30 minutes during off-peak hours (e.g., at 00:00) without degrading online system performance. | FR-SYS-01, FR-SYS-02 |
| NFR-PER-05 | The web application shall load its initial interface within 2.5 seconds for at least 95% of user requests under standard network conditions. | All |


### 2.3 Security

| ID | Requirement | Related FR |
|---|---|---|
| NFR-SEC-01 | The system shall store user passwords using a strong, salted hashing algorithm (e.g., Bcrypt with cost factor >= 12 or Argon2) and shall never store passwords in plain text. | FR-GST-04, FR-RDR-02 |
| NFR-SEC-02 | The system shall encrypt all communication between the user's client browser and the server using HTTPS over TLS v1.2 or TLS v1.3. | All |
| NFR-SEC-03 | The system shall enforce Role-Based Access Control (RBAC). A user shall not be able to access functions or data outside their assigned role permissions, including direct URL manipulation. | FR-ADM-02 |
| NFR-SEC-04 | A Reader shall be restricted to viewing only their own personal profile, borrowing history, and fine details. | FR-RDR-02, FR-RDR-06, FR-RDR-07 |
| NFR-SEC-05 | The system shall automatically terminate a user session after 30 minutes of inactivity. | FR-GST-04 |
| NFR-SEC-06 | The system shall temporarily lock an account for 15 minutes after 5 consecutive failed login attempts to prevent brute-force attacks. | FR-GST-04 |
| NFR-SEC-07 | The system shall sanitize and validate all user inputs to protect against common web vulnerabilities, including SQL Injection, Cross-Site Scripting (XSS), and CSRF. | All |
| NFR-SEC-08 | The system logs of Librarian and Administrator actions shall be write-once/read-only (immutable via the application), and shall only be viewable by an Administrator. | FR-SYS-04, FR-ADM-07 |
| NFR-SEC-09 | The system shall not store any credit card, bank, or e-wallet account credentials. All payment processing shall be delegated securely to third-party payment gateways. | FR-RDR-08 |
| NFR-SEC-10 | Only authenticated and authorized Readers with active accounts shall be permitted to read online or download digital course materials (E-books). | FR-RDR-09 |

### 2.4 Reliability, Availability, and Data Integrity

| ID | Requirement | Related FR |
|---|---|---|
| NFR-REL-01 | The system shall maintain an uptime availability of at least 99.5% during library operational hours, excluding scheduled maintenance windows. | All |
| NFR-REL-02 | The system shall enforce transactional ACID properties. If a borrowing or returning transaction fails midway, the system shall perform an automatic rollback to prevent partial or inconsistent data. | FR-LIB-06, FR-LIB-07 |
| NFR-REL-03 | The system shall implement database concurrency control (e.g., pessimistic locking) to prevent race conditions when two Librarians attempt to process the exact same book copy simultaneously. | FR-LIB-06 |
| NFR-REL-04 | The system shall perform automated daily database backups at 00:00 and store copies in two physically isolated locations (e.g., local backup server and cloud storage). | FR-ADM-05 |
| NFR-REL-05 | Following a hardware or system failure, the system shall achieve a Recovery Time Objective (RTO) of <= 4 hours and a Recovery Point Objective (RPO) of <= 24 hours. | FR-ADM-06 |
| NFR-REL-06 | The system shall handle notification dispatching asynchronously with automated retry mechanisms, ensuring that notification delivery failures do not block core system transactions. | FR-SYS-02 |

### 2.5 Usability

| ID | Requirement | Related FR |
|---|---|---|
| NFR-USA-01 | The primary user interface language shall be Vietnamese, using UTF-8 character encoding across all displays, forms, and database transactions. | All |
| NFR-USA-02 | A newly recruited Librarian shall be able to perform standard borrowing and returning transactions without supervision after at most 4 hours (half a day) of system training. | FR-LIB-06, FR-LIB-07 |
| NFR-USA-03 | The system shall display clear, actionable, and non-technical error messages that state the cause of the issue and guide the user on how to proceed. | All |
| NFR-USA-04 | The public portal (Guest and Reader interfaces) shall feature a responsive design that displays correctly across major desktop and mobile web browsers (Chrome, Safari, Firefox, Edge) down to a viewport width of 360px. | FR-GST-02, FR-RDR-06, FR-RDR-09 |
| NFR-USA-05 | The system shall require explicit user confirmation via modal dialogs before executing non-reversible or destructive actions (e.g., retiring books, locking accounts, or modifying global configuration). | FR-LIB-05, FR-LIB-12, FR-ADM-01, FR-ADM-03 |

### 2.6 Compatibility and Localization

| ID | Requirement | Related FR |
|---|---|---|
| NFR-COM-01 | The web application shall be fully compatible with the latest two major stable versions of major web browsers (Google Chrome, Microsoft Edge, Mozilla Firefox, Apple Safari) on both desktop and mobile platforms. | All |
| NFR-COM-02 | The system shall interface seamlessly with standard USB/Bluetooth barcode scanners operating in Human Interface Device (HID) / Keyboard Wedge emulation mode. | FR-LIB-06, FR-LIB-07, FR-LIB-13 |
| NFR-COM-03 | The system shall fully support Vietnamese localization (L10n), utilizing UTF-8 character encoding, formatting dates as DD/MM/YYYY, displaying currency in VND, and synchronizing timestamps with the Indochina Time zone (UTC+7). | All |
| NFR-COM-04 | The digital library component shall support processing, online rendering, and downloading of digital course materials in standard PDF and EPUB file formats. | FR-RDR-09 |

### 2.7 Maintainability and Scalability

| ID | Requirement | Related FR |
|---|---|---|
| NFR-MNT-01 | The system architecture shall follow a modular design (e.g., Layered Architecture / MVC) ensuring low coupling and high cohesion, so that modifications in one module (e.g., User, Catalog, Circulation, Report) do not impact others. | All |
| NFR-MNT-02 | Global business parameters (e.g., maximum borrowing limits, loan duration, daily overdue fine rates) shall be dynamically configurable via the Administrator interface without requiring source code modifications or system redeployment. | FR-ADM-03 |
| NFR-MNT-03 | The codebase shall adhere strictly to established industry coding standards, maintain comprehensive inline documentation, and provide clean API specifications to facilitate onboarding for new developers. | All |
| NFR-MNT-04 | The database schema and indexing strategy shall be designed to scale seamlessly, supporting at least 100,000 book records, 10,000 active Reader accounts, and up to 500,000 transaction logs without architectural redesign. | All |


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

The whole system is drawn as one process, `0.0 Library Management System`, connected to four external entities.

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

Process 0.0 is split into five processes. Each process uses the data store drawn below it.

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
| All | NFR-SEC-07, NFR-USA-01, NFR-COM-03 | Input is validated. The interface is in Vietnamese (UTF-8), dates use DD/MM/YYYY, currency is VND. |

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

### 5.2 Class Descriptions

| Class | Description | DFD Store | Related FR |
|---|---|---|---|
| `Role` | Defines user roles (`roleId`, `roleName`, `permissions`) to check access permissions. | D1 | FR-ADM-02 |
| `User` | Base class for all accounts (`userId`, `fullName`, `email`, `phone`, `passwordHash`, `avatarUrl`, `status`, `failedLogins`, `lockedUntil`) with login and profile methods. | D1 | FR-GST-01, FR-GST-04, FR-RDR-02 |
| `Reader` | Inherits from `User`. Adds `cardCode` and methods for reserving books, requesting renewals, and paying fines. | D1 | FR-RDR-01 to FR-RDR-09 |
| `Librarian` | Inherits from `User`. Provides methods to manage books, physical copies, counter borrowing/returning, and fines. | D1 | FR-LIB-01 to FR-LIB-13 |
| `Administrator` | Inherits from `User`. Provides methods to manage staff accounts, roles, system rules, backups, and logs. | D1 | FR-ADM-01 to FR-ADM-07 |
| `Book` | Contains book information (`bookId`, `isbn`, `ddcCode`, `title`, `author`, `category`, `ebookUrl`, `availableCopies`). | D2 | FR-GST-02, FR-RDR-09, FR-LIB-01 to FR-LIB-03 |
| `BookCopy` | A physical copy of a book on the shelf (`copyId`, `barcode`, `shelfLocation`, `status`, `condition`). | D2 | FR-LIB-04, FR-LIB-05, FR-LIB-13 |
| `BorrowRecord` | Records a borrowing transaction (`borrowId`, `borrowDate`, `dueDate`, `returnDate`, `returnCondition`, `renewCount`, `status`). | D3 | FR-RDR-04 to FR-RDR-06, FR-LIB-06 to FR-LIB-08 |
| `Reservation` | Keeps track of online book holds and waiting queues (`reservationId`, `reserveDate`, `expireDate`, `status`). | D3 | FR-RDR-03, FR-SYS-03 |
| `Fine` | Records a reader violation and its payment status (`fineId`, `reason`, `amount`, `isPaid`, `paymentMethod`, `transactionRef`, `paidAt`). | D4 | FR-RDR-07, FR-RDR-08, FR-LIB-09, FR-LIB-10, FR-SYS-01 |
| `SystemConfig` | Stores library settings (`configKey`, `configValue`, `updatedAt`) such as borrowing limits and daily fine rates. | D5 | FR-ADM-03 |
| `Notification` | Stores reminder messages (`notificationId`, `channel`, `message`, `status`, `sentAt`) sent to Readers. | D5 | FR-SYS-02 |
| `AuditLog` | Saves read-only logs of actions taken by Librarians and Administrators (`logId`, `action`, `targetId`, `createdAt`). | D5 | FR-ADM-07, FR-SYS-04 |


## 6. Data Model

### 6.1 Overview

The database uses UTF-8 (`utf8mb4`) encoding and consists of 10 relational tables corresponding to the five data stores (`D1` to `D5`) in Section 3.2.

### 6.2 Mapping to DFD Data Stores

| DFD Store | Mapped Database Tables |
|---|---|
| **D1** (User Accounts & Cards) | `roles`, `users` |
| **D2** (Book Catalog & Inventory) | `books`, `book_copies` |
| **D3** (Borrowing & Reservations) | `borrow_records`, `reservations` |
| **D4** (Fines & Violation Records) | `fines` |
| **D5** (System Logs & Configurations) | `system_configs`, `notifications`, `audit_logs` |

### 6.3 Table Specifications

#### 1. `roles` (Store D1)
Stores user roles and their permissions.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `role_id` | INT | PK, AUTO_INCREMENT | Role ID |
| `role_name` | VARCHAR(50) | UNIQUE, NOT NULL | `READER`, `LIBRARIAN`, `ADMIN` |
| `permissions` | TEXT | NOT NULL | List of allowed permissions |

#### 2. `users` (Store D1)
Stores user account details and library card codes.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `user_id` | INT | PK, AUTO_INCREMENT | User ID |
| `role_id` | INT | FK (`roles.role_id`), NOT NULL | Assigned role |
| `card_code` | VARCHAR(30) | UNIQUE, NULL | Library card barcode |
| `full_name` | VARCHAR(100) | NOT NULL | Full name |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | Email address |
| `phone` | VARCHAR(15) | UNIQUE, NOT NULL | Phone number |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt password hash |
| `avatar_url` | VARCHAR(255) | NULL | Link to avatar image |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | `PENDING`, `ACTIVE`, `LOCKED` |
| `failed_logins` | INT | DEFAULT 0 | Number of failed login attempts |
| `locked_until` | DATETIME | NULL | Time when temporary lock ends |

#### 3. `books` (Store D2)
Stores general book information and e-book links.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `book_id` | INT | PK, AUTO_INCREMENT | Book ID |
| `isbn` | VARCHAR(20) | UNIQUE, NOT NULL | ISBN code |
| `ddc_code` | VARCHAR(20) | NOT NULL | DDC classification code |
| `title` | VARCHAR(255) | NOT NULL | Book title |
| `author` | VARCHAR(150) | NOT NULL | Author name |
| `category` | VARCHAR(100) | NOT NULL | Book category |
| `ebook_url` | VARCHAR(255) | NULL | Path to PDF/EPUB file |
| `available_copies` | INT | DEFAULT 0 | Number of copies currently available |

#### 4. `book_copies` (Store D2)
Stores individual physical copies for barcode scanning.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `copy_id` | INT | PK, AUTO_INCREMENT | Copy ID |
| `book_id` | INT | FK (`books.book_id`), NOT NULL | Links to `books` |
| `barcode` | VARCHAR(50) | UNIQUE, NOT NULL | Barcode printed on the book |
| `shelf_location` | VARCHAR(50) | NOT NULL | Shelf location in storage |
| `status` | VARCHAR(20) | DEFAULT 'AVAILABLE' | `AVAILABLE`, `BORROWED`, `RESERVED`, `CANCELED` |
| `condition` | VARCHAR(20) | DEFAULT 'INTACT' | `INTACT`, `DAMAGED`, `LOST` |

#### 5. `borrow_records` (Store D3)
Stores borrowing, returning, and renewal history.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `borrow_id` | INT | PK, AUTO_INCREMENT | Borrow record ID |
| `user_id` | INT | FK (`users.user_id`), NOT NULL | Reader who borrowed the book |
| `copy_id` | INT | FK (`book_copies.copy_id`), NOT NULL | Borrowed physical copy |
| `librarian_id` | INT | FK (`users.user_id`), NOT NULL | Librarian who created the record |
| `borrow_date` | DATETIME | NOT NULL | Borrow date and time |
| `due_date` | DATETIME | NOT NULL | Expected return date |
| `return_date` | DATETIME | NULL | Actual return date |
| `return_condition` | VARCHAR(20) | NULL | Book condition when returned |
| `renew_count` | INT | DEFAULT 0 | Times renewed |
| `status` | VARCHAR(20) | DEFAULT 'BORROWED' | `BORROWED`, `RETURNED`, `OVERDUE` |

#### 6. `reservations` (Store D3)
Stores online book reservations and waiting lists.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `reservation_id` | INT | PK, AUTO_INCREMENT | Reservation ID |
| `user_id` | INT | FK (`users.user_id`), NOT NULL | Reader who reserved the book |
| `book_id` | INT | FK (`books.book_id`), NOT NULL | Reserved book title |
| `copy_id` | INT | FK (`book_copies.copy_id`), NULL | Assigned copy when returned |
| `reserve_date` | DATETIME | NOT NULL | Time of reservation |
| `expire_date` | DATETIME | NULL | Last day to pick up the book |
| `status` | VARCHAR(20) | DEFAULT 'WAITING' | `WAITING`, `READY`, `COMPLETED`, `CANCELED` |

#### 7. `fines` (Store D4)
Stores violation records and fine payments.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `fine_id` | INT | PK, AUTO_INCREMENT | Fine ID |
| `borrow_id` | INT | FK (`borrow_records.borrow_id`), NOT NULL | Related borrow record |
| `user_id` | INT | FK (`users.user_id`), NOT NULL | Reader who received the fine |
| `reason` | VARCHAR(50) | NOT NULL | `LATE_RETURN`, `DAMAGED`, `LOST` |
| `amount` | DECIMAL(10,2) | NOT NULL | Fine amount in VND |
| `is_paid` | BOOLEAN | DEFAULT FALSE | Paid status (`TRUE` or `FALSE`) |
| `payment_method` | VARCHAR(30) | NULL | `COUNTER` or `ONLINE` |
| `transaction_ref` | VARCHAR(100) | NULL | Payment gateway reference code |
| `paid_at` | DATETIME | NULL | Time of payment |

#### 8. `system_configs` (Store D5)
Stores library settings that the Administrator can change.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `config_key` | VARCHAR(50) | PK | `MAX_BOOKS`, `MAX_DAYS`, `DAILY_FINE`, `HOLD_DAYS` |
| `config_value` | VARCHAR(100) | NOT NULL | Setting value |
| `updated_at` | DATETIME | NOT NULL | Last updated time |

#### 9. `notifications` (Store D5)
Stores automatic reminders sent to Readers.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `notification_id` | INT | PK, AUTO_INCREMENT | Notification ID |
| `user_id` | INT | FK (`users.user_id`), NOT NULL | Reader receiving the message |
| `channel` | VARCHAR(20) | NOT NULL | `EMAIL`, `SMS`, `IN_APP` |
| `message` | TEXT | NOT NULL | Message text |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | `PENDING`, `SENT`, `FAILED` |
| `sent_at` | DATETIME | NULL | Time sent |

#### 10. `audit_logs` (Store D5)
Stores read-only logs of Librarian and Administrator actions.

| Column | Type | Key / Constraints | Description |
|---|---|---|---|
| `log_id` | INT | PK, AUTO_INCREMENT | Log ID |
| `actor_id` | INT | FK (`users.user_id`), NOT NULL | Librarian or Admin who did the action |
| `action` | VARCHAR(100) | NOT NULL | Action type (e.g., `EDIT_BOOK`, `LOCK_USER`) |
| `target_id` | VARCHAR(50) | NOT NULL | ID of the affected record |
| `created_at` | DATETIME | NOT NULL | Time of action |

## 7. Interface Design Description

*(To be updated)*
