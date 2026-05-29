"""Run once to populate the database with sample data."""
import hashlib
import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'quantumstudy.db')


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def seed():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------------
    # Subjects (14 subjects)
    # ------------------------------------------------------------------
    subjects_data = [
        ('Kazakh',             '#E8823A'),
        ('English',            '#9E9E9E'),
        ('Russian',            '#E84444'),
        ('Kazakh Literature',  '#C17A3E'),
        ('Russian Literature', '#E8A87C'),
        ('Kazakh History',     '#8B5E3C'),
        ('World History',      '#D4C137'),
        ('Geography',          '#5B9BD5'),
        ('Math',               '#7BC8E8'),
        ('Further Math',       '#4A90D9'),
        ('Computer Science',   '#1A3A6B'),
        ('Physics',            '#2EB8B8'),
        ('Chemistry',          '#9B59B6'),
        ('Biology',            '#4CAF50'),
    ]

    for name, color in subjects_data:
        exists = conn.execute('SELECT id FROM subject WHERE name=?', (name,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO subject (name, color, type) VALUES (?,?,?)',
                         (name, color, 'both'))

    # ------------------------------------------------------------------
    # Teacher users
    # ------------------------------------------------------------------
    teacher_users = [
        ('Maksat Nazarbek',    'maksat@quantum.study',    'teacher', 'Experienced educator in Sciences and Mathematics.'),
        ('Medetkhan Altynbek', 'medetkhan@quantum.study', 'teacher', 'Language specialist with 5+ years of teaching experience.'),
        ('Yerzhan Auerov',     'yerzhan@quantum.study',   'teacher', 'Graduate tutor specializing in Humanities.'),
    ]

    teacher_ids = []
    for name, email, role, bio in teacher_users:
        existing = conn.execute('SELECT id FROM user WHERE email=?', (email,)).fetchone()
        if existing:
            uid = existing['id']
        else:
            conn.execute(
                'INSERT INTO user (name, email, password_hash, grade, class, role) VALUES (?,?,?,?,?,?)',
                (name, email, hash_password('teacher123'), None, None, role)
            )
            conn.commit()
            uid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Create teacher entry (linked to all subjects)
        existing_teacher = conn.execute('SELECT id FROM teacher WHERE user_id=?', (uid,)).fetchone()
        if not existing_teacher:
            conn.execute('INSERT INTO teacher (user_id, subject_id, bio) VALUES (?,?,?)',
                         (uid, None, bio))
            conn.commit()
        tid = conn.execute('SELECT id FROM teacher WHERE user_id=?', (uid,)).fetchone()[0]
        teacher_ids.append(tid)

    # ------------------------------------------------------------------
    # Test student account
    # ------------------------------------------------------------------
    student_email = 'student@test.com'
    existing_student = conn.execute('SELECT id FROM user WHERE email=?', (student_email,)).fetchone()
    if not existing_student:
        conn.execute(
            'INSERT INTO user (name, email, password_hash, grade, class, role) VALUES (?,?,?,?,?,?)',
            ('Marlen Alua', student_email, hash_password('password'), 11, 'A', 'student')
        )
        conn.commit()
        student_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    else:
        student_id = existing_student['id']

    # ------------------------------------------------------------------
    # Sample lessons
    # ------------------------------------------------------------------
    lessons_data = [
        ('Computer Science', teacher_ids[0], 'online',  '17 April', '16:00', 8),
        ('Math',             teacher_ids[1], 'online',  '18 April', '14:00', 10),
        ('Physics',          teacher_ids[0], 'offline', '19 April', '10:00', 6),
        ('English',          teacher_ids[2], 'online',  '20 April', '15:00', 12),
        ('Biology',          teacher_ids[1], 'offline', '21 April', '11:00', 5),
        ('Chemistry',        teacher_ids[0], 'online',  '22 April', '09:00', 8),
    ]

    lesson_ids = []
    for subj_name, tid, ltype, date, time, slots in lessons_data:
        subj = conn.execute('SELECT id FROM subject WHERE name=?', (subj_name,)).fetchone()
        if not subj:
            continue
        existing_lesson = conn.execute(
            'SELECT id FROM lesson WHERE subject_id=? AND teacher_id=? AND date=? AND time=?',
            (subj['id'], tid, date, time)
        ).fetchone()
        if not existing_lesson:
            conn.execute(
                'INSERT INTO lesson (subject_id, teacher_id, type, date, time, slots_available) VALUES (?,?,?,?,?,?)',
                (subj['id'], tid, ltype, date, time, slots)
            )
            conn.commit()
            lid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        else:
            lid = existing_lesson['id']
        lesson_ids.append(lid)

    # ------------------------------------------------------------------
    # Sample bookings for test student
    # ------------------------------------------------------------------
    for lid in lesson_ids[:3]:
        existing_booking = conn.execute(
            'SELECT id FROM booking WHERE user_id=? AND lesson_id=?', (student_id, lid)
        ).fetchone()
        if not existing_booking:
            conn.execute(
                'INSERT INTO booking (user_id, lesson_id, booked_at) VALUES (?,?,?)',
                (student_id, lid, '2024-04-15T12:00:00')
            )

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------
    products = [
        ('Classic Hoodie',    'boys',  4500, ''),
        ('Sport Jacket',      'boys',  5200, ''),
        ('Casual Tee',        'boys',  1800, ''),
        ('Denim Shirt',       'boys',  3200, ''),
        ('Floral Dress',      'girls', 4800, ''),
        ('Knit Sweater',      'girls', 3600, ''),
        ('Summer Blouse',     'girls', 2400, ''),
        ('Striped Cardigan',  'girls', 3900, ''),
    ]
    for name, cat, price, img in products:
        exists = conn.execute('SELECT id FROM product WHERE name=?', (name,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO product (name, category, price, image_path) VALUES (?,?,?,?)',
                         (name, cat, price, img))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    events = [
        ('Science Olympiad',     '2024-05-10', '10:00', 'Annual school science competition for grades 9-11.'),
        ('Math Challenge Cup',   '2024-05-15', '14:00', 'Inter-class mathematics tournament. All grades welcome.'),
        ('Literature Evening',   '2024-05-20', '17:00', 'Student poetry and prose readings in Kazakh and Russian.'),
        ('IT Hackathon',         '2024-05-25', '09:00', 'Build an app in 8 hours. Teams of 2-4 students.'),
        ('Sports Day',           '2024-06-01', '08:00', 'School-wide athletics and team sports event.'),
        ('Graduation Ceremony',  '2024-06-15', '16:00', 'Celebration for graduating Class 11 students.'),
    ]
    for title, date, time, desc in events:
        exists = conn.execute('SELECT id FROM event WHERE title=?', (title,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO event (title, date, time, description) VALUES (?,?,?,?)',
                         (title, date, time, desc))

    conn.commit()
    conn.close()
    print('✓ Database seeded successfully.')
    print('  Test login → email: student@test.com  password: password')
    print('  Teacher login → email: maksat@quantum.study  password: teacher123')


if __name__ == '__main__':
    # Ensure tables exist
    from app import init_db
    init_db()
    seed()
