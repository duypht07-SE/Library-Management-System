
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
