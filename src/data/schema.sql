PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    role           VARCHAR(20)  NOT NULL CHECK (role IN ('READER', 'LIBRARIAN', 'ADMIN')),
    card_code      VARCHAR(30)  UNIQUE,
    student_id     VARCHAR(30)  UNIQUE,
    full_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(100) NOT NULL UNIQUE,
    phone          VARCHAR(15)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    avatar_path    VARCHAR(255),
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(20)  NOT NULL DEFAULT 'PENDING'
                   CHECK (status IN ('PENDING', 'ACTIVE', 'LOCKED', 'REJECTED')),
    failed_logins  INTEGER      NOT NULL DEFAULT 0,
    locked_until   DATETIME
);

CREATE TABLE IF NOT EXISTS books (
    book_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn      VARCHAR(20)  NOT NULL UNIQUE,
    ddc_code  VARCHAR(20)  NOT NULL,
    title     VARCHAR(255) NOT NULL,
    author    VARCHAR(150) NOT NULL,
    category  VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS book_copies (
    copy_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id         INTEGER     NOT NULL REFERENCES books (book_id),
    barcode         VARCHAR(50) NOT NULL UNIQUE,
    shelf_location  VARCHAR(50) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
                    CHECK (status IN ('AVAILABLE', 'BORROWED', 'RESERVED', 'CANCELED')),
    copy_condition  VARCHAR(20) NOT NULL DEFAULT 'INTACT'
                    CHECK (copy_condition IN ('INTACT', 'DAMAGED', 'LOST'))
);

CREATE TABLE IF NOT EXISTS borrow_records (
    borrow_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    reader_id         INTEGER  NOT NULL REFERENCES users (user_id),
    copy_id           INTEGER  NOT NULL REFERENCES book_copies (copy_id),
    librarian_id      INTEGER  NOT NULL REFERENCES users (user_id),
    borrow_date       DATETIME NOT NULL,
    due_date          DATETIME NOT NULL,
    return_date       DATETIME,
    return_condition  VARCHAR(20) CHECK (return_condition IN ('INTACT', 'DAMAGED', 'LOST')),
    renew_count       INTEGER  NOT NULL DEFAULT 0,
    status            VARCHAR(20) NOT NULL DEFAULT 'BORROWED'
                      CHECK (status IN ('BORROWED', 'OVERDUE', 'RETURNED'))
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    reader_id       INTEGER  NOT NULL REFERENCES users (user_id),
    book_id         INTEGER  NOT NULL REFERENCES books (book_id),
    copy_id         INTEGER  REFERENCES book_copies (copy_id),
    reserve_date    DATETIME NOT NULL,
    expire_date     DATETIME,
    status          VARCHAR(20) NOT NULL DEFAULT 'WAITING'
                    CHECK (status IN ('WAITING', 'READY', 'COMPLETED', 'CANCELED'))
);

CREATE TABLE IF NOT EXISTS fines (
    fine_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    borrow_id  INTEGER       NOT NULL REFERENCES borrow_records (borrow_id),
    reason     VARCHAR(50)   NOT NULL CHECK (reason IN ('LATE_RETURN', 'DAMAGED', 'LOST')),
    amount     DECIMAL(12,0) NOT NULL CHECK (amount > 0),
    is_paid    BOOLEAN       NOT NULL DEFAULT 0,
    paid_at    DATETIME
);

CREATE TABLE IF NOT EXISTS system_configs (
    config_key    VARCHAR(50)  PRIMARY KEY
                  CHECK (config_key IN ('MAX_BOOKS', 'MAX_DAYS', 'MAX_RENEW', 'HOLD_DAYS', 'DAILY_FINE')),
    config_value  VARCHAR(100) NOT NULL,
    updated_by    INTEGER      NOT NULL REFERENCES users (user_id),
    updated_at    DATETIME     NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    reader_id        INTEGER     NOT NULL REFERENCES users (user_id),
    channel          VARCHAR(20) NOT NULL DEFAULT 'IN_APP' CHECK (channel IN ('IN_APP')),
    message          TEXT        NOT NULL,
    status           VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                     CHECK (status IN ('PENDING', 'SENT', 'FAILED')),
    sent_at          DATETIME
);

CREATE INDEX IF NOT EXISTS idx_books_title      ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author     ON books (author);
CREATE INDEX IF NOT EXISTS idx_books_category   ON books (category);
CREATE INDEX IF NOT EXISTS idx_copies_book      ON book_copies (book_id, status);
CREATE INDEX IF NOT EXISTS idx_borrow_reader    ON borrow_records (reader_id, status);
CREATE INDEX IF NOT EXISTS idx_borrow_due       ON borrow_records (status, due_date);
CREATE INDEX IF NOT EXISTS idx_reservation_book ON reservations (book_id, status, reserve_date);
CREATE INDEX IF NOT EXISTS idx_fines_borrow     ON fines (borrow_id, is_paid);
CREATE INDEX IF NOT EXISTS idx_fines_paid_at    ON fines (paid_at, is_paid);
