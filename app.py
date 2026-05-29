import os
import sqlite3
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, session, url_for)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'quantumstudy-secret-2024')

DATABASE = os.path.join(os.path.dirname(__file__), 'quantumstudy.db')
GEMINI_KEY = os.getenv('GEMINI_API_KEY', '')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            class TEXT,
            grade INTEGER,
            role TEXT DEFAULT 'student'
        );
        CREATE TABLE IF NOT EXISTS subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT,
            type TEXT
        );
        CREATE TABLE IF NOT EXISTS teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            bio TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (subject_id) REFERENCES subject(id)
        );
        CREATE TABLE IF NOT EXISTS lesson (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_id INTEGER,
            type TEXT,
            date TEXT,
            time TEXT,
            slots_available INTEGER DEFAULT 10,
            FOREIGN KEY (subject_id) REFERENCES subject(id),
            FOREIGN KEY (teacher_id) REFERENCES teacher(id)
        );
        CREATE TABLE IF NOT EXISTS booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            lesson_id INTEGER,
            booked_at TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (lesson_id) REFERENCES lesson(id)
        );
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            image_path TEXT
        );
        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT,
            time TEXT,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS chat_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
    ''')
    conn.commit()
    conn.close()


def hash_password(pw):
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def slug(name):
    return name.lower().replace(' ', '-')


def name_from_slug(s):
    return s.replace('-', ' ').title()


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        grade = request.form.get('grade', '')
        cls = request.form.get('class', '')
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO user (name, email, password_hash, grade, class) VALUES (?,?,?,?,?)',
                (name, email, hash_password(password), grade, cls)
            )
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email'].strip().lower()
    password = request.form['password']
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM user WHERE email=? AND password_hash=?',
        (email, hash_password(password))
    ).fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return redirect(url_for('dashboard'))
    flash('Invalid email or password.', 'error')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ── Main pages ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    upcoming = conn.execute('''
        SELECT l.date, l.time, s.name AS subject_name, s.color, l.type
        FROM booking b
        JOIN lesson l ON b.lesson_id = l.id
        JOIN subject s ON l.subject_id = s.id
        WHERE b.user_id = ?
        ORDER BY l.date, l.time
        LIMIT 6
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', upcoming=upcoming)


@app.route('/personal')
@login_required
def personal():
    conn = get_db()
    bookings = conn.execute('''
        SELECT l.date, l.time, s.name AS subject_name, s.color, l.type,
               u.name AS teacher_name
        FROM booking b
        JOIN lesson l ON b.lesson_id = l.id
        JOIN subject s ON l.subject_id = s.id
        JOIN teacher t ON l.teacher_id = t.id
        JOIN user u ON t.user_id = u.id
        WHERE b.user_id = ?
        ORDER BY l.date, l.time
    ''', (session['user_id'],)).fetchall()
    conn.close()

    grade_table = [
        (1,  'A',     'D E F G'),
        (2,  'A',     'D E F G'),
        (3,  'A',     'D E F G'),
        (4,  'A',     'D E f'),
        (5,  'A',     'D E F G H'),
        (6,  'A',     'D E F'),
        (7,  'A',     'D E F G'),
        (8,  'A',     'D E F G'),
        (9,  'A',     'D E F'),
        (10, 'A B',   'D E F G'),
        (11, 'A',     'D E F G'),
    ]
    return render_template('personal.html', bookings=bookings, grade_table=grade_table)


@app.route('/shop')
@login_required
def shop():
    conn = get_db()
    boys = conn.execute("SELECT * FROM product WHERE category='boys'").fetchall()
    girls = conn.execute("SELECT * FROM product WHERE category='girls'").fetchall()
    conn.close()
    return render_template('shop.html', boys=boys, girls=girls)


@app.route('/events')
@login_required
def events():
    conn = get_db()
    evts = conn.execute('SELECT * FROM event ORDER BY date, time').fetchall()
    conn.close()
    return render_template('events.html', events=evts)


# ── Lessons ───────────────────────────────────────────────────────────────────

SUBJECTS = [
    {'name': 'Kazakh',            'color': '#E8823A', 'dark': False},
    {'name': 'English',           'color': '#9E9E9E', 'dark': False},
    {'name': 'Russian',           'color': '#E84444', 'dark': False},
    {'name': 'Kazakh Literature', 'color': '#C17A3E', 'dark': False},
    {'name': 'Russian Literature','color': '#E8A87C', 'dark': True},
    {'name': 'Kazakh History',    'color': '#8B5E3C', 'dark': False},
    {'name': 'World History',     'color': '#D4C137', 'dark': True},
    {'name': 'Geography',         'color': '#5B9BD5', 'dark': False},
    {'name': '',                  'color': '',        'dark': False},  # empty cell
    {'name': 'Math',              'color': '#7BC8E8', 'dark': True},
    {'name': 'Further Math',      'color': '#4A90D9', 'dark': False},
    {'name': 'Computer Science',  'color': '#1A3A6B', 'dark': False},
    {'name': 'Physics',           'color': '#2EB8B8', 'dark': False},
    {'name': 'Chemistry',         'color': '#9B59B6', 'dark': False},
    {'name': 'Biology',           'color': '#4CAF50', 'dark': False},
]


@app.route('/lessons/online')
@login_required
def lessons_online():
    return render_template('lessons_grid.html', lesson_type='online', subjects=SUBJECTS)


@app.route('/lessons/offline')
@login_required
def lessons_offline():
    return render_template('lessons_grid.html', lesson_type='offline', subjects=SUBJECTS)


@app.route('/lessons/<subject_slug>')
@login_required
def subject_page(subject_slug):
    lesson_type = request.args.get('type', 'online')
    # Find matching subject
    subject = next((s for s in SUBJECTS if s['name'] and slug(s['name']) == subject_slug), None)
    if not subject:
        return redirect(url_for('lessons_online'))

    conn = get_db()
    teachers = conn.execute('''
        SELECT t.id, u.name, t.bio
        FROM teacher t
        JOIN user u ON t.user_id = u.id
    ''').fetchall()
    conn.close()

    chat_key = f'chat_{subject_slug}'
    chat_history = session.get(chat_key, [])

    return render_template('subject.html',
                           subject=subject,
                           subject_slug=subject_slug,
                           lesson_type=lesson_type,
                           teachers=teachers,
                           chat_history=chat_history)


@app.route('/lessons/<subject_slug>/book', methods=['POST'])
@login_required
def book_lesson(subject_slug):
    teacher_id = request.form.get('teacher_id')
    day = request.form.get('date_day', '1')
    month = request.form.get('date_month', 'January')
    hour = request.form.get('time_hour', '09')
    minute = request.form.get('time_minute', '00')
    lesson_type = request.form.get('lesson_type', 'online')

    date_str = f"{day} {month}"
    time_str = f"{hour}:{minute}"

    subject = next((s for s in SUBJECTS if s['name'] and slug(s['name']) == subject_slug), None)
    if not subject or not teacher_id:
        return redirect(url_for('subject_page', subject_slug=subject_slug))

    conn = get_db()
    # Get or create DB subject entry
    db_subject = conn.execute('SELECT id FROM subject WHERE name=?', (subject['name'],)).fetchone()
    if not db_subject:
        conn.execute('INSERT INTO subject (name, color, type) VALUES (?,?,?)',
                     (subject['name'], subject['color'], lesson_type))
        conn.commit()
        db_subject = conn.execute('SELECT id FROM subject WHERE name=?', (subject['name'],)).fetchone()

    subject_id = db_subject['id']

    # Get or create lesson
    lesson = conn.execute(
        'SELECT id FROM lesson WHERE subject_id=? AND teacher_id=? AND date=? AND time=? AND type=?',
        (subject_id, teacher_id, date_str, time_str, lesson_type)
    ).fetchone()

    if lesson:
        lesson_id = lesson['id']
    else:
        conn.execute(
            'INSERT INTO lesson (subject_id, teacher_id, type, date, time, slots_available) VALUES (?,?,?,?,?,10)',
            (subject_id, teacher_id, lesson_type, date_str, time_str)
        )
        conn.commit()
        lesson_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Check not already booked
    existing = conn.execute(
        'SELECT id FROM booking WHERE user_id=? AND lesson_id=?',
        (session['user_id'], lesson_id)
    ).fetchone()

    if not existing:
        conn.execute(
            'INSERT INTO booking (user_id, lesson_id, booked_at) VALUES (?,?,?)',
            (session['user_id'], lesson_id, datetime.now().isoformat())
        )
        conn.commit()
        flash('Lesson booked successfully!', 'success')
    else:
        flash('You have already booked this lesson.', 'info')

    conn.close()
    return redirect(url_for('personal'))


# ── AI Tutor ──────────────────────────────────────────────────────────────────

@app.route('/ai/ask', methods=['POST'])
@login_required
def ai_ask():
    data = request.get_json()
    subject_name = data.get('subject', 'General')
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'answer': 'Please type a question.'})

    chat_key = f'chat_{slug(subject_name)}'
    history = session.get(chat_key, [])
    history.append({'role': 'user', 'content': question})

    answer = ''
    if GEMINI_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')

            system = (
                f"You are a helpful tutor for {subject_name}. "
                f"Explain concepts clearly for high school students. "
                f"Answer only questions related to {subject_name}. "
                f"Be concise and educational. Use simple language."
            )

            # Build prompt with recent history
            prompt_parts = [system, '\n\n']
            for msg in history[-12:]:
                role_label = 'Student' if msg['role'] == 'user' else 'Tutor'
                prompt_parts.append(f"{role_label}: {msg['content']}\n")
            prompt_parts.append('Tutor:')

            response = model.generate_content(''.join(prompt_parts))
            answer = response.text.strip()
        except Exception as e:
            answer = f'Sorry, I encountered an error: {str(e)}'
    else:
        answer = ('AI Tutor is not configured. '
                  'Please add your GEMINI_API_KEY to the .env file.')

    history.append({'role': 'assistant', 'content': answer})
    session[chat_key] = history
    session.modified = True

    # Persist to DB
    conn = get_db()
    conn.execute(
        'INSERT INTO chat_message (user_id, subject, role, content, created_at) VALUES (?,?,?,?,?)',
        (session['user_id'], subject_name, 'user', question, datetime.now().isoformat())
    )
    conn.execute(
        'INSERT INTO chat_message (user_id, subject, role, content, created_at) VALUES (?,?,?,?,?)',
        (session['user_id'], subject_name, 'assistant', answer, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({'answer': answer})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
