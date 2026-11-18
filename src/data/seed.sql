-- Sample data. Every account uses the password in README.md; {{PASSWORD_HASH}} is filled in by Seeder.

INSERT INTO users (user_id, role, card_code, student_id, full_name, email, phone, password_hash, status) VALUES
    (1, 'ADMIN',     NULL,      'STF-0001', 'Nguyen Thanh Admin', 'admin@library.test',      '0900000001', '{{PASSWORD_HASH}}', 'ACTIVE'),
    (2, 'LIBRARIAN', NULL,      'STF-0002', 'Tran Thi Lan',       'librarian@library.test',  '0900000002', '{{PASSWORD_HASH}}', 'ACTIVE'),
    (3, 'READER',    'RD-0001', '22520001', 'Nguyen Van An',      'reader@library.test',     '0900000003', '{{PASSWORD_HASH}}', 'ACTIVE'),
    (4, 'READER',    'RD-0002', '22520002', 'Le Thi Binh',        'reader2@library.test',    '0900000004', '{{PASSWORD_HASH}}', 'ACTIVE'),
    (5, 'READER',    NULL,      '22520003', 'Pham Minh Chau',     'pending@library.test',    '0900000005', '{{PASSWORD_HASH}}', 'PENDING'),
    (6, 'READER',    'RD-0003', '22520004', 'Hoang Duc Dung',     'locked@library.test',     '0900000006', '{{PASSWORD_HASH}}', 'LOCKED'),
    (7, 'READER',    'RD-0004', '22520005', 'Vo Thi Em',          'reader3@library.test',    '0900000007', '{{PASSWORD_HASH}}', 'ACTIVE');

INSERT INTO books (book_id, isbn, ddc_code, title, author, category) VALUES
    (1,  '9780132350884', '005.1',  'Clean Code',                        'Robert C. Martin',      'Computer Science'),
    (2,  '9780133943030', '005.1',  'Software Engineering',              'Ian Sommerville',       'Computer Science'),
    (3,  '9780133970777', '005.74', 'Database Systems',                  'Elmasri, Navathe',      'Computer Science'),
    (4,  '9786040000011', '515',    'Calculus 1',                        'Nguyen Dinh Tri',       'Mathematics'),
    (5,  '9786040000028', '005.133','Java Programming Basics',           'Pham Van At',           'Computer Science'),
    (6,  '9780262046305', '006.3',  'Introduction to Algorithms',        'Cormen et al.',         'Computer Science'),
    (7,  '9786040000035', '512.5',  'Linear Algebra',                    'Nguyen Huu Viet Hung',  'Mathematics'),
    (8,  '9780134870960', '519.5',  'Probability and Statistics',        'Walpole et al.',        'Mathematics'),
    (9,  '9781292152639', '330',    'Principles of Economics',           'N. Gregory Mankiw',     'Economics'),
    (10, '9780134472089', '332',    'Corporate Finance',                 'Berk, DeMarzo',         'Economics'),
    (11, '9786040000042', '340',    'Introduction to Vietnamese Law',    'Le Minh Tam',           'Law'),
    (12, '9786040000059', '346.07', 'Civil Law Basics',                  'Do Van Dai',            'Law'),
    (13, '9780521532891', '428',    'English Grammar in Use',            'Raymond Murphy',        'Languages'),
    (14, '9784789014403', '495.6',  'Japanese for Beginners',            'Minna no Nihongo',      'Languages'),
    (15, '9786040000066', '895.922','The Tale of Kieu',                  'Nguyen Du',             'Literature'),
    (16, '9780061120084', '813',    'To Kill a Mockingbird',             'Harper Lee',            'Literature'),
    (17, '9786040000073', '959.7',  'History of Vietnam',                'Tran Trong Kim',        'History'),
    (18, '9780062316097', '909',    'Sapiens',                           'Yuval Noah Harari',     'History'),
    (19, '9786040000080', '895.9223','Diary of a Cricket',               'To Hoai',               'Children''s books'),
    (20, '9780140328721', '823',    'Matilda',                           'Roald Dahl',            'Children''s books');

-- Two copies per book: copy_id 1-20 are the first copies, 21-40 the second copies
INSERT INTO book_copies (book_id, barcode, shelf_location)
    SELECT book_id, printf('LIB-%05d', book_id * 10 + 1), printf('A%02d-1', book_id) FROM books ORDER BY book_id;
INSERT INTO book_copies (book_id, barcode, shelf_location)
    SELECT book_id, printf('LIB-%05d', book_id * 10 + 2), printf('A%02d-2', book_id) FROM books ORDER BY book_id;

INSERT INTO borrow_records (borrow_id, reader_id, copy_id, librarian_id, borrow_date, due_date, return_date, return_condition, status) VALUES
    (1, 3, 1,  2, datetime('now', '+7 hours', '-5 days'),  datetime('now', '+7 hours', '+9 days'),  NULL, NULL, 'BORROWED'),
    (2, 4, 2,  2, datetime('now', '+7 hours', '-20 days'), datetime('now', '+7 hours', '-6 days'),  NULL, NULL, 'OVERDUE'),
    (3, 3, 3,  2, datetime('now', '+7 hours', '-30 days'), datetime('now', '+7 hours', '-16 days'), datetime('now', '+7 hours', '-13 days'), 'INTACT', 'RETURNED'),
    (4, 4, 4,  2, datetime('now', '+7 hours', '-40 days'), datetime('now', '+7 hours', '-26 days'), datetime('now', '+7 hours', '-27 days'), 'INTACT', 'RETURNED'),
    (5, 4, 5,  2, datetime('now', '+7 hours', '-3 days'),  datetime('now', '+7 hours', '+11 days'), NULL, NULL, 'BORROWED'),
    (6, 7, 21, 2, datetime('now', '+7 hours', '-2 days'),  datetime('now', '+7 hours', '+12 days'), NULL, NULL, 'BORROWED');

UPDATE book_copies SET status = 'BORROWED' WHERE copy_id IN (1, 2, 5, 21);
UPDATE book_copies SET status = 'RESERVED' WHERE copy_id = 25;

INSERT INTO reservations (reservation_id, reader_id, book_id, copy_id, reserve_date, expire_date, status) VALUES
    (1, 3, 5, 25,   datetime('now', '+7 hours', '-4 days'), datetime('now', '+7 hours', '+2 days'), 'READY'),
    (2, 4, 1, NULL, datetime('now', '+7 hours', '-1 days'), NULL, 'WAITING');

INSERT INTO fines (fine_id, borrow_id, reason, amount, is_paid) VALUES
    (1, 3, 'LATE_RETURN', 15000, 0);

INSERT INTO notifications (reader_id, channel, message, status, sent_at) VALUES
    (3, 'IN_APP', 'Java Programming Basics is ready for pickup. Please collect it within 3 days.', 'SENT', datetime('now', '+7 hours', '-1 days')),
    (4, 'IN_APP', 'Software Engineering is overdue. Please return it to the library desk.',       'SENT', datetime('now', '+7 hours'));

INSERT INTO system_configs (config_key, config_value, updated_by, updated_at) VALUES
    ('MAX_BOOKS',  '5',    1, datetime('now', '+7 hours')),
    ('MAX_DAYS',   '14',   1, datetime('now', '+7 hours')),
    ('MAX_RENEW',  '1',    1, datetime('now', '+7 hours')),
    ('HOLD_DAYS',  '3',    1, datetime('now', '+7 hours')),
    ('DAILY_FINE', '5000', 1, datetime('now', '+7 hours'));
