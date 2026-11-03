📚 Library Management System (LMS) — Group 06

Course Project: Software Engineering

📌 PROJECT OVERVIEW

The Library Management System (LMS) is a software application designed to manage a university's digital library and automate its book borrowing and returning processes.

The system addresses three core business domains:

1. Book Catalog Search & Management
Manage two levels of book information: Book Titles and physical Book Copies, each identified by a unique Barcode/RFID tag.
Integrate a digital library that supports reading and downloading E-books in PDF/EPUB formats.
Provide comprehensive book search and catalog management functionalities.
2. Automated Circulation & Borrowing Management
Support fast book check-in and check-out operations at the library counter using barcode scanning.
Allow readers to renew borrowed books.
Enable online book reservations and hold management.
Handle violations and overdue fines.
3. Administration & Automation
Implement Role-Based Access Control (RBAC) for user permission management.
Provide dynamic configuration of library policies and borrowing regulations.
Automatically calculate overdue fines at 00:00 (midnight).
Send automated reminders and notifications.
Generate statistical reports to support library management.

📂 REPOSITORY DIRECTORY STRUCTURE
Library-Management-System/
│
├── docs/
│   └── Requirements_and_Design.md
│
├── diagrams/
│   ├── dfd_level0.drawio
│   ├── dfd_level1.drawio
│   ├── usecase_diagram.puml
│   ├── class_diagram.puml
│   └── erd_schema.drawio
│
├── ui/
│   ├── screen_guest_search.png
│   ├── screen_librarian_counter.png
│   ├── screen_reader_profile.png
│   └── screen_admin_config.png
│
└── README.md


📑 SYSTEM SPECIFICATIONS

The detailed system design documentation is located in docs/Requirements_and_Design.md and consists of seven standardized sections:

1. Functional Requirements (FR)

The system includes 37 Functional Requirements distributed across five actors:

Guest (4 FRs):
Search the public book catalog.
View library news and regulations.
Register a new account.
Log in to the system.
Reader (9 FRs):
Manage personal profiles.
Reserve books online.
Renew borrowed books.
View borrowing history and outstanding fines.
Make online fine payments.
Read digital E-books.
Librarian (13 FRs):
Manage the book inventory using DDC classification and ISBN.
Perform book check-in/check-out operations using barcode scanning.
Create violation records.
Collect fine payments.
Approve and suspend library membership cards.
Conduct physical inventory checks.
Administrator (7 FRs):
Manage librarian accounts.
Configure Role-Based Access Control (RBAC).
Dynamically configure borrowing policies and fine regulations.
Generate and export reports.
Perform database backup and recovery.
Review system Audit Logs.
System (4 FRs):
Automatically calculate overdue fines through background jobs at 00:00.
Send automated reminders via Email, SMS, and in-app notifications.
Automatically cancel expired reservations.
Record system activity logs.
2. Non-Functional Requirements (NFR)

The system specifies 34 measurable Non-Functional Requirements across six quality attributes:

Performance (5 NFRs):
Book search response time ≤ 2.0 seconds for a catalog of 100,000 books.
Library counter transaction processing time ≤ 2.0 seconds.
Page loading time ≤ 2.5 seconds.
Support at least 100 concurrent users.
Security (10 NFRs):
Secure password hashing with unique salts.
Encrypted data transmission using HTTPS/TLS.
Role-Based Access Control (RBAC).
Temporary account locking after multiple failed login attempts.
Immutable Audit Logs.
Reliability (6 NFRs):
System availability ≥ 99.5%.
ACID-compliant transactions with rollback support.
Pessimistic Locking to prevent conflicting borrowing transactions.
Recovery Time Objective (RTO) ≤ 4 hours.
Recovery Point Objective (RPO) ≤ 24 hours.
Usability (5 NFRs):
Vietnamese user interface with UTF-8 encoding.
New librarian training time ≤ 4 hours.
Responsive web design supporting screens down to 360px.
Confirmation modal dialogs for critical or potentially destructive operations.
Compatibility (4 NFRs):
Compatibility with the two latest versions of supported browsers.
Support for HID barcode scanners.
Vietnamese localization, including DD/MM/YYYY date format, VND currency, and UTC+7 timezone.
Support for PDF and EPUB E-book formats.
Maintainability (4 NFRs):
Layered/MVC architecture following Low Coupling and High Cohesion principles.
Clean Code practices and API specifications.
Database scalability to support at least 100,000 books.
3. Data Flow Diagram (DFD)

DFD Level 0 (Context Diagram):

A central process, Process 0.0, interacts with five external entities:
Guest
Reader
Librarian
Administrator
Payment Gateway
The system consists of five data stores:
D1: Users & Cards
D2: Book Catalog
D3: Borrowing & Reservations
D4: Fines & Violations
D5: Logs & Configurations

DFD Level 1 (Process Decomposition):

The central system is decomposed into six main processes:

1.0 — User Authentication
2.0 — Catalog Management
3.0 — Circulation Management
4.0 — Fines & Payments
5.0 — Administration & Reports
6.0 — Background Jobs
4. Use Case Diagram

The Use Case Diagram illustrates the interactions between system actors and their corresponding functionalities.

Generalization Relationships:
Reader, Librarian, and Administrator inherit from the general User actor.
All specialized actors inherit the common Login functionality.
Relationships:
<<include>> is used for mandatory authentication and other required sub-functions.
<<extend>> is used for optional or exceptional workflows.
Example: Record Violation extends Check In Books when returned books are overdue, damaged, or lost.
5. Class Diagram (Object-Oriented Design)

The Class Diagram represents the system's object-oriented structure and relationships between its main classes.

The primary classes include:

User (Abstract Class)
Reader
Librarian
Administrator
Book
BookCopy
BorrowRecord
Reservation
Fine
Notification
SystemConfig
6. Data Model (3NF Relational Database)

The system uses a relational database schema designed according to Third Normal Form (3NF) principles.

Key database characteristics:

UTF-8 character encoding using utf8mb4.
Relational database support for MySQL/PostgreSQL.
Structured relationships between entities.
Reduced data redundancy and improved data integrity.

The database consists of eight main tables:

users
books
book_copies
borrow_records
reservations
fines
system_configs
notifications
7. Interface Design

This section describes the system's UI/UX design specifications, including:

UI/UX design guidelines and color palette.
Application navigation flow.
Wireframes and detailed mockups for core system screens.
Responsive interface design for desktop and mobile devices.
🛠️ TECHNOLOGY STACK & STANDARDS
Component	Technology / Applicable Standards
Requirements Specification	IEEE Std 830-1998 (Software Requirements Specification)
System Modeling	UML 2.5 (Use Case Diagram, Class Diagram) using PlantUML and Draw.io
Database	Relational Database Schema (MySQL / PostgreSQL), 3NF, UTF-8
Security	Secure Password Hashing, HTTPS / TLS 1.2+, RBAC
UI/UX Design	Responsive Web Design (Desktop & Mobile down to 360px), Figma / Draw.io
Version Control	Git & GitHub
👥 TEAM MEMBERS & RESPONSIBILITIES

**Group 06 — Software Engineering Course Project**

| No. | Full Name | Responsibilities |
|:---:|---|---|
| 1 | Phạm Hồ Thanh Duy | Project Introduction, Functional Requirements, and Non-Functional Requirements |
| 2 | Võ Đức Thắng | Design of Data Flow Diagrams (DFD Level 0 and Level 1) and Use Case Diagram |
| 3 | Lê Phước Sang | Design of Class Diagram |
| 4 | Nguyễn Đức Tài | Design of Data Model |

📖 HOW TO USE
1. Access the Full Documentation

Open the following file in the GitHub repository:

text
docs/Requirements_and_Design.md


This file contains the complete requirements specification and detailed system design documentation.

2. Edit and Export UML Diagrams
Open .puml files using the PlantUML extension in Visual Studio Code or an online tool such as PlantText.
Open .drawio files using Draw.io.
Edit and export diagrams as needed.
3. Contribute and Update the Project
All documentation changes must be submitted through a Pull Request (PR).
Contributors should provide clear descriptions of their changes.
Every modification must be recorded in the Document Revision History table.
Follow the team's Git and GitHub version control workflow to maintain project consistency.

Group 06 — Library Management System (LMS)

Software Engineering Course Project
