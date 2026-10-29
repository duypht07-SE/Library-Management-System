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
| FR-GST-01 | The system shall allow a Guest to register an account, or to request a library card, by entering personal information (full name, email, phone number, etc.). |
| FR-GST-02 | The system shall allow a Guest to search public books by title, author, or category and to see whether a book is still available or out of stock. A Guest shall not be able to borrow or reserve a book. |
| FR-GST-03 | The system shall allow a Guest to view the library's regulations, opening hours, events, and latest news. |
| FR-GST-04 | The system shall allow a Guest to log in by entering an account and a password, and shall then give the user the role of Reader, Librarian, or Administrator according to the account. |

### 1.3 Reader

| ID | Requirement |
|---|---|
| FR-RDR-01 | The system shall give a Reader all functions of a Guest (searching books and viewing library information). |
| FR-RDR-02 | The system shall allow a Reader to view and update personal information, including changing the password, updating the avatar, and changing the phone number or contact email. |
| FR-RDR-03 | The system shall allow a Reader to reserve a book online, whether the book is on the shelf or currently borrowed by another Reader. |
| FR-RDR-04 | The system shall allow a Reader to send a renewal request, asking for more borrowing time, for books that are close to their due date. |
| FR-RDR-05 | The system shall approve a renewal request only if the book has not been reserved by another Reader. |
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
| FR-LIB-07 | The system shall allow a Librarian to record a returned book by scanning its barcode, so that the book is updated back into stock. |
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

### 1.6 System (Automatic Functions)

| ID | Requirement |
|---|---|
| FR-SYS-01 | The system shall scan all borrowing records periodically every day (for example at 00:00) and, for each overdue record, automatically add the fine to the Reader's account. |
| FR-SYS-02 | The system shall automatically send reminders to Readers by email, SMS, or in-app notification when a book is due soon (2 days before the due date), when a book is overdue, or when a reserved book is available on the shelf for pickup. |
| FR-SYS-03 | The system shall automatically cancel a reservation hold if the Reader does not pick up the book within X days (for example 3 days) after the book is placed on the waiting shelf, and shall return the book to the available state for other Readers. |
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
| NFR-PER-01 | The system shall return book search results within 3 seconds under normal load. | FR-GST-02 |
| NFR-PER-02 | The system shall save a borrowing or returning transaction and show the result to the Librarian within 2 seconds after the barcode is scanned. | FR-LIB-06, FR-LIB-07 |
| NFR-PER-03 | The system shall support at least 100 users using the system at the same time without a noticeable drop in response time. | All |
| NFR-PER-04 | The daily scan of borrowing records (fine calculation and reminders) shall finish within 30 minutes and shall not slow down the services used by Readers and Librarians. | FR-SYS-01, FR-SYS-02 |

### 2.3 Security

| ID | Requirement | Related FR |
|---|---|---|
| NFR-SEC-01 | The system shall store passwords in hashed form, never as plain text. | FR-GST-04, FR-RDR-02 |
| NFR-SEC-02 | The system shall transmit data between the user's browser and the server over HTTPS. | All |
| NFR-SEC-03 | The system shall enforce role-based access control. A user shall not be able to access functions or data outside the permissions of their role, even by typing a function's address directly. | FR-ADM-02 |
| NFR-SEC-04 | A Reader shall be able to view only their own personal information, borrowing history, and fines. | FR-RDR-02, FR-RDR-06, FR-RDR-07 |
| NFR-SEC-05 | The system shall automatically log a user out after 30 minutes of inactivity. | FR-GST-04 |
| NFR-SEC-06 | The system shall temporarily lock a login after 5 consecutive failed attempts. | FR-GST-04 |
| NFR-SEC-07 | The system shall validate all user input to protect against common attacks such as SQL injection and cross-site scripting (XSS). | All |
| NFR-SEC-08 | The system log of Librarian and Administrator actions shall not be editable or deletable through the application, and only an Administrator shall be able to view it. | FR-SYS-04 |
| NFR-SEC-09 | The system shall not store the bank or e-wallet account details of a Reader. Online payment shall be handled by the payment gateway. | FR-RDR-08 |
| NFR-SEC-10 | Only logged-in Readers shall be able to read or download e-books. | FR-RDR-09 |

### 2.4 Reliability, Availability, and Data Integrity

| ID | Requirement | Related FR |
|---|---|---|
| NFR-REL-01 | The system shall be available at least 99% of the time during the library's opening hours. | All |
| NFR-REL-02 | The system shall keep borrowing records, book status, and the number of available copies consistent. If a borrowing or returning transaction fails halfway, the system shall cancel the whole transaction and shall not leave partial data. | FR-LIB-06, FR-LIB-07 |
| NFR-REL-03 | The system shall prevent two Librarians from borrowing the same copy of a book at the same time. | FR-LIB-06 |
| NFR-REL-04 | The system shall be backed up at least once a day. | FR-ADM-05 |
| NFR-REL-05 | The system shall be restorable from the latest backup within 4 hours after a technical failure, with a loss of no more than one day of data. | FR-ADM-06 |
| NFR-REL-06 | If a notification (email, SMS, or in-app) cannot be sent, the system shall retry and shall record the failure, without stopping other tasks. | FR-SYS-02 |

### 2.5 Usability

| ID | Requirement | Related FR |
|---|---|---|
| NFR-USA-01 | The user interface shall be in Vietnamese. | All |
| NFR-USA-02 | A new Librarian shall be able to perform the borrowing and returning operations after at most half a day of training. | FR-LIB-06, FR-LIB-07 |
| NFR-USA-03 | The system shall show clear, understandable error messages that tell the user what went wrong and what to do next. | All |
| NFR-USA-04 | The Reader and Guest pages shall display correctly on both desktop and mobile browsers. | FR-GST-02, FR-RDR-06 |
| NFR-USA-05 | The system shall ask for confirmation before a destructive action, such as retiring a book or locking an account. | FR-LIB-05, FR-LIB-12, FR-ADM-01 |

### 2.6 Compatibility and Localization

| ID | Requirement | Related FR |
|---|---|---|
| NFR-COM-01 | The system shall work on the latest versions of Chrome, Edge, Firefox, and Safari. | All |
| NFR-COM-02 | The system shall work with a standard barcode scanner connected to the computer, which sends the scanned code as keyboard input. | FR-LIB-06, FR-LIB-07, FR-LIB-13 |
| NFR-COM-03 | The system shall store and display Vietnamese text correctly (UTF-8), and shall display dates in the format dd/mm/yyyy using the time zone UTC+7. | All |
| NFR-COM-04 | The system shall support e-book files in PDF and EPUB format. | FR-RDR-09 |

### 2.7 Maintainability and Scalability

| ID | Requirement | Related FR |
|---|---|---|
| NFR-MNT-01 | The system shall be divided into separate modules (for example account, book, borrowing, and report), so that a change in one module affects the others as little as possible. | All |
| NFR-MNT-02 | Library parameters (maximum books per Reader, maximum borrowing days, and fine per day) shall be changeable through the system without modifying the source code. | FR-ADM-03 |
| NFR-MNT-03 | The source code shall follow a consistent naming and coding convention and shall be documented well enough for a new team member to understand it. | All |
| NFR-MNT-04 | The system shall handle at least 100,000 book records and 10,000 Reader accounts without a change in system design. | All |


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
