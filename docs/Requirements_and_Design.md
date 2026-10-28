# Software Requirements Specification and Design Document
**Project Name:** Library Management System (LMS)

## 1. Functional Requirements

The Library Management System (LMS) is designed to support the basic operations of a library, including book searching, reader account management, book inventory management, borrowing and returning books, and report generation.

The system distinguishes between a **BookTitle**, which represents a book title or edition, and a **BookCopy**, which represents an individual physical copy. Each physical copy has a unique barcode and an individual circulation status.

The system supports four user roles: **Guest, Reader, Librarian, and Administrator**. Each role has access to functions according to its permissions.

In this document, the word **“shall”** indicates a mandatory system requirement.

### 1.1 Book Searching and Browsing

| ID | Requirement |
|---|---|
| FR-SRC-01 | The system shall allow users to browse book titles by category. |
| FR-SRC-02 | The system shall allow users to search for book titles by title, author, or ISBN and display the results using pagination. |
| FR-SRC-03 | The system shall allow users to sort search results by publication year, title, or borrowing popularity. |
| FR-SRC-04 | The system shall display book-title details, including BookTitle ID, ISBN, title, author, publisher, publication year, category, cover image, and description, when available. |
| FR-SRC-05 | The system shall display the total number of physical copies and the number of available copies for each book title. |
| FR-SRC-06 | The system shall display the shelf location and circulation status of each physical copy to authorized staff. |

### 1.2 Account and Reader Card Management

| ID | Requirement |
|---|---|
| FR-ACC-01 | The system shall allow a Guest to register for a Reader account by providing the required personal information, including full name, student ID or identity card number, phone number, email address, and password. |
| FR-ACC-02 | The system shall allow registered users to log in using their registered credentials. |
| FR-ACC-03 | The system shall allow registered users to log out of the system. |
| FR-ACC-04 | The system shall provide a password recovery process for registered users. The specific recovery method shall depend on the implementation scope. |
| FR-ACC-05 | The system shall allow a Reader to view their profile and update permitted information, such as phone number and address. |
| FR-ACC-06 | The system shall assign each Reader a unique Reader ID and record the library card's issue date, expiration date, and status. |
| FR-ACC-07 | The system shall allow a Librarian to activate or block a Reader's library card according to library regulations. |
| FR-ACC-08 | The system shall allow authorized staff to view and search Reader information. |

### 1.3 Book Circulation

| ID | Requirement |
|---|---|
| FR-CIR-01 | Before creating a loan, the system shall check whether the Reader's account and library card are active and whether the Reader satisfies the applicable borrowing rules. |
| FR-CIR-02 | The system shall allow a Librarian to create a loan by entering or scanning a Reader ID and the barcode of each physical BookCopy. |
| FR-CIR-03 | For each loan, the system shall record the Loan ID, Reader ID, Librarian ID, borrowing date, due date, loan status, and the physical book copies included in the transaction. |
| FR-CIR-04 | The system shall prevent a physical BookCopy from being borrowed if its circulation status is not AVAILABLE. |
| FR-CIR-05 | After a borrowing transaction is confirmed, the system shall change the borrowed BookCopy status from AVAILABLE to LOANED and update the available-copy count of the corresponding book title. |
| FR-CIR-06 | The system shall allow a Librarian to process returned books and record the actual return date and physical condition of each returned BookCopy. |
| FR-CIR-07 | After a BookCopy is returned in acceptable condition, the system shall update its status to AVAILABLE and update the available-copy count. Copies that are lost or unusable shall not be counted as available. |
| FR-CIR-08 | The system shall identify overdue loans by comparing the due date with the current date and checking whether the associated BookCopy has been returned. |
| FR-CIR-09 | The system shall calculate overdue fines according to the library's approved fine policy. |
| FR-CIR-10 | The system shall record lost or severely damaged BookCopy cases and calculate compensation according to the library's approved compensation policy. |
| FR-CIR-11 | The system shall allow a Reader to view their borrowing history and the status of their loans. |
| FR-CIR-12 | If online reservations are included in the approved project scope, the system shall allow a Reader to place and cancel a reservation according to the applicable reservation rules. |

### 1.4 System Administration and Inventory Management

| ID | Requirement |
|---|---|
| FR-ADM-01 | The system shall allow authorized staff to create and update book-title records. |
| FR-ADM-02 | The system shall allow authorized staff to manage physical BookCopy records, including each copy's unique barcode, shelf location, and circulation status. |
| FR-ADM-03 | The system shall allow authorized staff to mark a book title or physical BookCopy as inactive or unavailable when it should no longer be circulated. |
| FR-ADM-04 | The system shall prevent a book title or physical BookCopy from being permanently deleted if deletion would affect active loans or historical borrowing records. |
| FR-ADM-05 | The system shall allow authorized staff to view, create, update, and deactivate Reader and Librarian accounts according to their permissions. |
| FR-ADM-06 | The system shall enforce role-based permissions for Guest, Reader, Librarian, and Administrator roles. |
| FR-ADM-07 | The system shall allow a Librarian to record fine payments and print a receipt when fine collection is included in the approved project scope. |
| FR-ADM-08 | The system shall generate basic library reports, including the total number of book titles, total physical copies, available copies, active loans, overdue loans, and registered Readers. |
| FR-ADM-09 | The system shall allow authorized staff to view monthly library statistics based on the available borrowing and inventory records. |

### 1.5 Data Validation and Error Handling

| ID | Requirement |
|---|---|
| FR-VAL-01 | The system shall validate required fields before saving book-title, BookCopy, Reader, or loan information. |
| FR-VAL-02 | The system shall prevent duplicate values for identifiers that must be unique, including Reader ID, student ID or identity card number, BookCopy barcode, and Loan ID. |
| FR-VAL-03 | The system shall validate ISBN format and uniqueness according to the book catalog's data rules. |
| FR-VAL-04 | The system shall prevent borrowing transactions when the Reader is blocked, the library card is expired, or the selected BookCopy is unavailable. |
| FR-VAL-05 | The system shall display clear error messages when users enter invalid information or attempt unauthorized operations. |
| FR-VAL-06 | The system shall maintain consistency between loan records, physical-copy statuses, and available-copy counts when books are borrowed or returned. |

### 1.6 Proposed Business Rules (Pending Confirmation)

The following business rules are proposed for the project and have not yet been confirmed by the project team or instructor. They shall be treated as configurable or provisional rules until approval.

| ID | Proposed Business Rule | Status |
|---|---|---|
| BR-CIR-01 | A Reader classified as a Student may borrow a maximum of 5 books at a time. | Proposed; pending confirmation |
| BR-CIR-02 | The standard loan duration is 14 days. | Proposed; pending confirmation |
| BR-CIR-03 | The overdue fine is 5,000 VND per overdue day per book. | Proposed; pending confirmation |
| BR-CIR-04 | Compensation for a lost or severely damaged book is 100% of the book's recorded price plus a 20,000 VND processing fee. | Proposed; pending confirmation |
| BR-ACC-01 | A library card issued to a Reader classified as a Student is valid for 1 year by default. | Proposed; pending confirmation |

The project team shall confirm these rules with the instructor before treating them as final requirements. If any rule is not approved, the corresponding requirement and its related diagrams, database design, and test cases shall be updated accordingly.

Closes #1

## 2. Non-Functional Requirements
*(To be updated)*

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
