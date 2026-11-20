"""
College Complaint & Resolution System - Database Module
Handles SQLite connection, schema initialization, and demo data seeding.
"""

import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Determine absolute path to database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'instance', 'complaints.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')


def get_db_path():
    """Return database file path."""
    return os.environ.get('COMPLAINTS_DB_PATH', DEFAULT_DB_PATH)


def get_db():
    """
    Open database connection with Row factory and foreign keys enabled.
    """
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """
    Initialize database using schema.sql and seed demo data if tables are empty.
    """
    if db_path is None:
        db_path = get_db_path()

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

        # Check if users table already has data
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            seed_demo_data(conn)
            print("Database initialized and demo accounts seeded successfully.")
        else:
            print("Database already contains data; skipping initial seed.")


def seed_demo_data(conn):
    """
    Populate database with default departments, demo accounts, and sample complaints.
    """
    cursor = conn.cursor()

    # 1. Insert Departments
    departments = [
        ('Hostel Administration', 'HOSTEL', 'Hostel accommodation, rooms, water supply, and residential facilities'),
        ('IT & Network Support', 'WIFI', 'Campus Wi-Fi connectivity, computer labs, portal access, and network infrastructure'),
        ('Campus Maintenance & Infrastructure', 'MAINT', 'Electrical fittings, plumbing, carpentry, air conditioning, and building maintenance'),
        ('Academic & Classroom Facilities', 'CLASS', 'Classroom projectors, smart boards, benches, lighting, and lecture hall utilities'),
        ('General Administration', 'ADMIN', 'General campus amenities, cleanliness, cafeteria, and miscellaneous grievances')
    ]

    cursor.executemany(
        "INSERT INTO departments (name, code, description) VALUES (?, ?, ?)",
        departments
    )

    # Fetch inserted department IDs
    cursor.execute("SELECT id, code FROM departments")
    dept_map = {row['code']: row['id'] for row in cursor.fetchall()}

    # 2. Insert Demo Users
    # Passwords hashed with Werkzeug
    pw_admin = generate_password_hash('admin123')
    pw_staff = generate_password_hash('staff123')
    pw_student = generate_password_hash('student123')

    users = [
        # Admin
        ('admin', pw_admin, 'Dr. Arvind Swaminathan', 'admin@college.edu', 'admin', None, '9876543210', None),
        
        # Staff members
        ('staff_hostel', pw_staff, 'Rajesh Kumar (Hostel Warden)', 'warden.hostel@college.edu', 'staff', dept_map.get('HOSTEL'), '9876543211', None),
        ('staff_it', pw_staff, 'Anil Sharma (Network Engineer)', 'anil.it@college.edu', 'staff', dept_map.get('WIFI'), '9876543212', None),
        ('staff_maint', pw_staff, 'Suresh Patel (Maintenance Lead)', 'suresh.maint@college.edu', 'staff', dept_map.get('MAINT'), '9876543213', None),
        ('staff_class', pw_staff, 'Meera Nair (Facilities In-Charge)', 'meera.class@college.edu', 'staff', dept_map.get('CLASS'), '9876543214', None),

        # Students
        ('student1', pw_student, 'Aarav Sharma', 'aarav.sharma@college.edu', 'student', None, '9123456780', '2024CS101'),
        ('student2', pw_student, 'Priya Verma', 'priya.verma@college.edu', 'student', None, '9123456781', '2024EC204'),
        ('student3', pw_student, 'Rohan Gupta', 'rohan.gupta@college.edu', 'student', None, '9123456782', '2024ME312')
    ]

    cursor.executemany(
        """
        INSERT INTO users (username, password_hash, full_name, email, role, department_id, phone, roll_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        users
    )

    # Fetch inserted user IDs
    cursor.execute("SELECT id, username FROM users")
    user_map = {row['username']: row['id'] for row in cursor.fetchall()}

    # 3. Insert Sample Complaints across different lifecycle statuses
    # Complaint 1: Wi-Fi issue - In Progress
    cursor.execute(
        """
        INSERT INTO complaints (ticket_id, student_id, category, title, description, location, department_id, assigned_to, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            'CMP-2026-0001',
            user_map['student1'],
            'Wi-Fi',
            'No Internet Connectivity in Hostel Block B, 3rd Floor',
            'The Wi-Fi access point in the 3rd floor corridor has been showing a solid amber/red light since yesterday. Students cannot access course portals or online research databases.',
            'Hostel Block B, 3rd Floor Corridor',
            dept_map['WIFI'],
            user_map['staff_it'],
            'In Progress',
            '2026-11-18 10:30:00',
            '2026-11-19 14:15:00'
        )
    )
    c1_id = cursor.lastrowid

    # Updates for Complaint 1
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c1_id, user_map['student1'], 'Pending', 'Complaint submitted by student.', '2026-11-18 10:30:00')
    )
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c1_id, user_map['admin'], 'Assigned', 'Assigned to IT & Network Support department (Anil Sharma).', '2026-11-18 11:45:00')
    )
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c1_id, user_map['staff_it'], 'In Progress', 'Inspected 3rd-floor switch rack. Firmware reboot scheduled, replacing faulty PoE patch cord today.', '2026-11-19 14:15:00')
    )

    # Notifications for Complaint 1
    cursor.execute(
        "INSERT INTO notifications (user_id, complaint_id, message, is_read, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_map['staff_it'], c1_id, 'New complaint CMP-2026-0001 assigned to you: No Internet Connectivity in Hostel Block B', 1, '2026-11-18 11:45:00')
    )
    cursor.execute(
        "INSERT INTO notifications (user_id, complaint_id, message, is_read, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_map['student1'], c1_id, 'Your complaint CMP-2026-0001 status changed to In Progress.', 0, '2026-11-19 14:15:00')
    )

    # Complaint 2: Hostel Water Tap Leakage - Resolved with Feedback
    cursor.execute(
        """
        INSERT INTO complaints (ticket_id, student_id, category, title, description, location, department_id, assigned_to, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            'CMP-2026-0002',
            user_map['student2'],
            'Hostel',
            'Water Leakage from Bathroom Sink Tap in Room 204',
            'The sink faucet in bathroom 204 has a steady continuous leak causing water accumulation and slippery floor tiles.',
            'Girls Hostel 1, Room 204',
            dept_map['HOSTEL'],
            user_map['staff_hostel'],
            'Resolved',
            '2026-11-17 09:15:00',
            '2026-11-17 15:40:00'
        )
    )
    c2_id = cursor.lastrowid

    # Updates for Complaint 2
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c2_id, user_map['student2'], 'Pending', 'Complaint submitted by student.', '2026-11-17 09:15:00')
    )
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c2_id, user_map['admin'], 'Assigned', 'Assigned to Hostel Administration.', '2026-11-17 10:00:00')
    )
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c2_id, user_map['staff_hostel'], 'In Progress', 'Hostel maintenance plumber dispatched with replacement washers.', '2026-11-17 11:30:00')
    )
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c2_id, user_map['staff_hostel'], 'Resolved', 'Faucet washer and rubber gasket replaced. Water flow tested and completely sealed.', '2026-11-17 15:40:00')
    )

    # Feedback for Complaint 2
    cursor.execute(
        "INSERT INTO feedback (complaint_id, student_id, rating, comments, created_at) VALUES (?, ?, ?, ?, ?)",
        (c2_id, user_map['student2'], 5, 'Very quick turnaround by the hostel maintenance staff. Fixed within 6 hours. Thank you!', '2026-11-17 17:00:00')
    )

    # Notification for Complaint 2
    cursor.execute(
        "INSERT INTO notifications (user_id, complaint_id, message, is_read, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_map['student2'], c2_id, 'Your complaint CMP-2026-0002 has been marked as Resolved. Please provide feedback.', 1, '2026-11-17 15:40:00')
    )

    # Complaint 3: Classroom Projector Issue - Assigned
    cursor.execute(
        """
        INSERT INTO complaints (ticket_id, student_id, category, title, description, location, department_id, assigned_to, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            'CMP-2026-0003',
            user_map['student1'],
            'Classroom',
            'Ceiling Projector HDMI Port Damaged in Seminar Hall 2',
            'The HDMI input cable for the ceiling mounted projector is physically broken at the connector pin. Unable to connect laptops for presentations.',
            'Academic Block A, Seminar Hall 2',
            dept_map['CLASS'],
            user_map['staff_class'],
            'Assigned',
            '2026-11-19 16:00:00',
            '2026-11-20 09:00:00'
        )
    )
    c3_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c3_id, user_map['student1'], 'Pending', 'Complaint submitted by student.', '2026-11-19 16:00:00')
    )
    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c3_id, user_map['admin'], 'Assigned', 'Assigned to Academic & Classroom Facilities (Meera Nair).', '2026-11-20 09:00:00')
    )
    cursor.execute(
        "INSERT INTO notifications (user_id, complaint_id, message, is_read, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_map['staff_class'], c3_id, 'New complaint CMP-2026-0003 assigned: Projector HDMI Port Damaged', 0, '2026-11-20 09:00:00')
    )

    # Complaint 4: Maintenance - Pending (unassigned)
    cursor.execute(
        """
        INSERT INTO complaints (ticket_id, student_id, category, title, description, location, department_id, assigned_to, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            'CMP-2026-0004',
            user_map['student3'],
            'Maintenance',
            'Broken Bench Wooden Plank and Flickering Tube Light in Lab 4',
            'Row 3 Bench 5 wooden plank is split and has sharp nails exposed. Also two fluorescent tube lights above the blackboard are flickering continuously.',
            'Mechanical Block, CAD/CAM Lab 4',
            dept_map['MAINT'],
            None,
            'Pending',
            '2026-11-20 11:20:00',
            '2026-11-20 11:20:00'
        )
    )
    c4_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c4_id, user_map['student3'], 'Pending', 'Complaint submitted. Awaiting administrative assignment.', '2026-11-20 11:20:00')
    )

    # Complaint 5: Other - Pending
    cursor.execute(
        """
        INSERT INTO complaints (ticket_id, student_id, category, title, description, location, department_id, assigned_to, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            'CMP-2026-0005',
            user_map['student2'],
            'Other',
            'Water Cooler Filter Replacement Needed in Main Library',
            'The drinking water dispenser on the 1st floor of the central library has an unpleasant taste and filter replacement indicator is red.',
            'Central Library, 1st Floor Reading Hall',
            dept_map['ADMIN'],
            None,
            'Pending',
            '2026-11-20 12:45:00',
            '2026-11-20 12:45:00'
        )
    )
    c5_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO complaint_updates (complaint_id, user_id, status, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (c5_id, user_map['student2'], 'Pending', 'Complaint submitted by student.', '2026-11-20 12:45:00')
    )

    conn.commit()


# Helper functions for database operations
def add_notification(conn, user_id, complaint_id, message):
    """Insert a notification for a user."""
    conn.execute(
        "INSERT INTO notifications (user_id, complaint_id, message, is_read) VALUES (?, ?, ?, 0)",
        (user_id, complaint_id, message)
    )


def generate_ticket_id(conn):
    """Generate a unique complaint ticket ID (e.g. CMP-2026-0006)."""
    year = datetime.now().year
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0] + 1
    return f"CMP-{year}-{count:04d}"


if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database ready.")
