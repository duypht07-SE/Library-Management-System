Library Management System (LMS)
This repository contains the software requirements specification, architectural design, and system diagrams for an academic Library Management System (LMS) developed by Group 06.

The system automates core library operations, including physical book circulation using barcode scanning, digital e-book access, reservation queues, fine tracking, and automated background jobs.

Standards Applied
Software Requirements Specification: IEEE Std 830-1998
System Modeling: UML 2.5 (Use Case, Class Diagrams)
Database Normalization: Relational Schema in Third Normal Form (3NF)

System Overview & Architecture
The complete system specification is documented in docs/Requirements_and_Design.md across seven structured sections:

1. Functional Requirements (FR)
Includes 37 defined requirements organized by five system actors:

Guest (4 FRs): Public catalog search, account registration, library news, and login.
Reader (9 FRs): Profile management, online book reservation, loan renewals, borrowing history, online fine payment, and digital e-book reading (PDF/EPUB).
Librarian (13 FRs): Book cataloging (ISBN/DDC classification), barcode-based checkout/checkin, physical condition assessment, violation recording, on-site fine collection, card approvals, and inventory audits.
Administrator (7 FRs): Staff account management, role-based access control (RBAC), configuration of dynamic library parameters (max books, loan duration, daily fine rate), report generation, database backups, and audit log inspection.
System (4 FRs): Automated midnight cron job (00:00) for calculating overdue fines, notification dispatch (Email/SMS/In-app), automatic cancellation of uncollected holds after 3 days, and activity logging.
2. Non-Functional Requirements (NFR)
Specifies 34 measurable quality attributes across six categories:

Performance: Book search response time $\le 2.0$s for 100,000 records; checkout processing $\le 2.0$s; page load time $\le 2.5$s; 100 concurrent active users.
Security: Password hashing using Bcrypt/Argon2 with salt; HTTPS/TLS 1.2+ encryption; RBAC authorization; 15-minute account lock after 5 failed login attempts; OWASP threat mitigation; immutable audit logs.
Reliability: Uptime $\ge 99.5%$; ACID transaction compliance with automatic rollback; pessimistic locking for concurrent loan requests; daily automated backups at 00:00; RTO $\le 4$h, RPO $\le 24$h.
Usability: UTF-8 Vietnamese interface; responsive layout down to 360px viewport; new librarian training time $\le 4$h; explicit confirmation modals for destructive operations.
Compatibility: Supports current versions of major desktop/mobile browsers; compatible with HID barcode scanners; uses DD/MM/YYYY, VND, and UTC+7.
Maintainability: Layered/MVC modular architecture with low coupling; dynamic parameter configuration without redeployment; clean code guidelines; database capacity for 100,000 books and 10,000 users.
3. Data Flow Diagram (DFD)
Level 0 (Context Diagram): High-level boundary showing interactions between Process 0.0 and five external entities (Guest, Reader, Librarian, Admin, Payment Gateway).
Data Stores: Five logical stores (D1 Users & Cards, D2 Books & Catalog, D3 Borrowing & Holds, D4 Fines & Violations, D5 System Configs & Logs).
Level 1: Decomposed into six functional sub-processes (1.0 to 6.0).
4. Use Case Diagram
Actor Inheritance: Reader, Librarian, and Administrator inherit from the base User actor, inheriting the Log In use case.
Relationships: Uses <<include>> for mandatory sub-processes and <<extend>> for conditional workflows (e.g., Record Violation extending Check In Books when items are returned late or damaged).
5. Class Diagram
Defines 11 domain classes: User (Abstract base), Reader, Librarian, Administrator, Book, BookCopy, BorrowRecord, Reservation, Fine, Notification, and SystemConfig.
6. Relational Data Model (3NF)
Normalized relational database schema comprising 8 tables in Third Normal Form: users, books, book_copies, borrow_records, reservations, fines, system_configs, and notifications.
7. Interface Design
UI/UX guidelines, navigation flow diagrams, and wireframe mockups for key application screens.
Technical Stack & Tools
Component	Tool / Standard
Specification Standard	IEEE Std 830-1998
System Modeling	UML 2.5 via PlantUML & Draw.io
Database Architecture	Relational Schema (3NF), UTF-8 (utf8mb4)
Interface Design	Wireframes & Mockups (Figma / Draw.io)
Version Control	Git & GitHub
Working with Diagram Source Files
PlantUML Files (.puml):
Open .puml files in VS Code with the PlantUML extension installed, or paste the script into PlantText to render PNG/SVG diagrams.
Draw.io Files (.drawio):
Import .drawio files directly into draw.io to edit or export vector graphics.
