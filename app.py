"""
College Complaint & Resolution System
Flask Web Application
Backend routes, session authentication, and role-based access control.
"""

import os
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g, abort, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, init_db, add_notification, generate_ticket_id

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'college_complaint_system_secret_key_2026')

# Ensure database is initialized on startup
with app.app_context():
    init_db()


# ============================================================================
# Authentication & Authorization Helpers
# ============================================================================

def get_current_user():
    """Fetch logged in user record from database."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    user = db.execute(
        """
        SELECT u.*, d.name AS department_name, d.code AS department_code
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        WHERE u.id = ?
        """,
        (user_id,)
    ).fetchone()
    return user


@app.before_request
def load_logged_in_user():
    """Attach current user and unread notification count to Flask g object."""
    g.user = get_current_user()
    if g.user:
        db = get_db()
        unread_count = db.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (g.user['id'],)
        ).fetchone()[0]
        g.unread_notifications_count = unread_count
    else:
        g.unread_notifications_count = 0


@app.context_processor
def inject_global_vars():
    """Make current_user and helper values available in all Jinja2 templates."""
    return {
        'current_user': g.user,
        'unread_count': g.unread_notifications_count,
        'current_year': datetime.now().year
    }


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Decorator to restrict route access to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for('login'))
            if g.user['role'] not in roles:
                flash(f"Access denied. You do not have permission to view that page.", "danger")
                # Redirect user to their appropriate role dashboard
                if g.user['role'] == 'student':
                    return redirect(url_for('student_dashboard'))
                elif g.user['role'] == 'staff':
                    return redirect(url_for('staff_dashboard'))
                elif g.user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# Authentication Routes (Login & Logout)
# ============================================================================

@app.route('/')
def index():
    """Landing route: redirects authenticated users to their dashboard, else to login."""
    if g.user:
        if g.user['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        elif g.user['role'] == 'staff':
            return redirect(url_for('staff_dashboard'))
        elif g.user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with username and password validation."""
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html')

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            # Session assignment
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            session['full_name'] = user['full_name']

            flash(f"Welcome back, {user['full_name']}!", "success")

            # Redirect based on user role
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'staff':
                return redirect(url_for('staff_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password. Please verify your credentials.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Log out current user and clear session."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


# ============================================================================
# Student Module Routes
# ============================================================================

@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    """Student Dashboard: metrics, recent complaints, recent notifications."""
    db = get_db()
    student_id = g.user['id']

    # Statistics
    stats = {
        'total': db.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_id,)).fetchone()[0],
        'pending': db.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'Pending'", (student_id,)).fetchone()[0],
        'in_progress': db.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status IN ('Assigned', 'In Progress')", (student_id,)).fetchone()[0],
        'resolved': db.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status IN ('Resolved', 'Closed')", (student_id,)).fetchone()[0],
    }

    # Recent complaints
    recent_complaints = db.execute(
        """
        SELECT c.*, d.name AS department_name, f.id AS feedback_id, f.rating AS feedback_rating
        FROM complaints c
        LEFT JOIN departments d ON c.department_id = d.id
        LEFT JOIN feedback f ON c.id = f.complaint_id
        WHERE c.student_id = ?
        ORDER BY c.created_at DESC
        LIMIT 5
        """,
        (student_id,)
    ).fetchall()

    # Recent notifications
    recent_notifications = db.execute(
        """
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (student_id,)
    ).fetchall()

    return render_template(
        'student_dashboard.html',
        stats=stats,
        complaints=recent_complaints,
        notifications=recent_notifications
    )


@app.route('/student/submit-complaint', methods=['GET', 'POST'])
@role_required('student')
def submit_complaint():
    """Form to submit a new complaint."""
    db = get_db()

    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()

        # Validation
        valid_categories = ['Hostel', 'Classroom', 'Wi-Fi', 'Maintenance', 'Other']
        if category not in valid_categories:
            flash("Please select a valid complaint category.", "danger")
            departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
            return render_template('submit_complaint.html', departments=departments)

        if not title or len(title) < 5:
            flash("Complaint title must be at least 5 characters long.", "danger")
            departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
            return render_template('submit_complaint.html', departments=departments)

        if not description or len(description) < 10:
            flash("Please provide a detailed description (at least 10 characters).", "danger")
            departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
            return render_template('submit_complaint.html', departments=departments)

        # Smart default department mapping based on category
        cat_to_dept_code = {
            'Hostel': 'HOSTEL',
            'Wi-Fi': 'WIFI',
            'Maintenance': 'MAINT',
            'Classroom': 'CLASS',
            'Other': 'ADMIN'
        }
        dept_code = cat_to_dept_code.get(category, 'ADMIN')
        dept_row = db.execute("SELECT id FROM departments WHERE code = ?", (dept_code,)).fetchone()
        dept_id = dept_row['id'] if dept_row else None

        ticket_id = generate_ticket_id(db)

        # Insert complaint
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO complaints (ticket_id, student_id, category, title, description, location, department_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
            """,
            (ticket_id, g.user['id'], category, title, description, location, dept_id)
        )
        complaint_id = cursor.lastrowid

        # Insert initial activity timeline record
        cursor.execute(
            """
            INSERT INTO complaint_updates (complaint_id, user_id, status, comment)
            VALUES (?, ?, 'Pending', 'Complaint submitted by student and logged into system.')
            """,
            (complaint_id, g.user['id'])
        )

        # Create confirmation notification for student
        add_notification(
            db,
            g.user['id'],
            complaint_id,
            f"Your complaint {ticket_id} ({category}) has been submitted successfully."
        )

        # Notify administrators
        admins = db.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
        for admin in admins:
            add_notification(
                db,
                admin['id'],
                complaint_id,
                f"New complaint {ticket_id} filed by {g.user['full_name']} under {category}."
            )

        db.commit()

        flash(f"Complaint {ticket_id} submitted successfully! You can track its status below.", "success")
        return redirect(url_for('complaint_details', id=complaint_id))

    departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
    return render_template('submit_complaint.html', departments=departments)


@app.route('/student/complaints')
@role_required('student')
def student_complaints():
    """List all complaints submitted by the current student."""
    db = get_db()
    student_id = g.user['id']

    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()

    sql = """
        SELECT c.*, d.name AS department_name, f.id AS feedback_id, f.rating AS feedback_rating
        FROM complaints c
        LEFT JOIN departments d ON c.department_id = d.id
        LEFT JOIN feedback f ON c.id = f.complaint_id
        WHERE c.student_id = ?
    """
    params = [student_id]

    if status_filter:
        sql += " AND c.status = ?"
        params.append(status_filter)

    if category_filter:
        sql += " AND c.category = ?"
        params.append(category_filter)

    if search_query:
        sql += " AND (c.ticket_id LIKE ? OR c.title LIKE ? OR c.description LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    sql += " ORDER BY c.created_at DESC"
    complaints = db.execute(sql, params).fetchall()

    return render_template(
        'complaints.html',
        complaints=complaints,
        status_filter=status_filter,
        category_filter=category_filter,
        search_query=search_query,
        page_title="My Submitted Complaints",
        user_role="student"
    )


# ============================================================================
# Staff Module Routes
# ============================================================================

@app.route('/staff/dashboard')
@role_required('staff')
def staff_dashboard():
    """Staff Dashboard: department complaints, status breakdown, pending action items."""
    db = get_db()
    staff = g.user
    dept_id = staff['department_id']

    if not dept_id:
        flash("You are not assigned to any department. Please contact an Administrator.", "warning")

    # Metrics for staff department
    stats = {
        'total': db.execute("SELECT COUNT(*) FROM complaints WHERE department_id = ?", (dept_id,)).fetchone()[0] if dept_id else 0,
        'assigned_to_me': db.execute("SELECT COUNT(*) FROM complaints WHERE assigned_to = ?", (staff['id'],)).fetchone()[0],
        'in_progress': db.execute("SELECT COUNT(*) FROM complaints WHERE department_id = ? AND status = 'In Progress'", (dept_id,)).fetchone()[0] if dept_id else 0,
        'resolved': db.execute("SELECT COUNT(*) FROM complaints WHERE department_id = ? AND status IN ('Resolved', 'Closed')", (dept_id,)).fetchone()[0] if dept_id else 0,
        'pending': db.execute("SELECT COUNT(*) FROM complaints WHERE department_id = ? AND status IN ('Pending', 'Assigned')", (dept_id,)).fetchone()[0] if dept_id else 0,
    }

    # Department complaints requiring action
    dept_complaints = db.execute(
        """
        SELECT c.*, u.full_name AS student_name, u.email AS student_email, u.phone AS student_phone,
               staff.full_name AS assigned_staff_name
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        WHERE c.department_id = ?
        ORDER BY CASE c.status
            WHEN 'In Progress' THEN 1
            WHEN 'Assigned' THEN 2
            WHEN 'Pending' THEN 3
            ELSE 4
        END, c.created_at DESC
        LIMIT 8
        """,
        (dept_id,)
    ).fetchall() if dept_id else []

    # Recent notifications
    notifications = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (staff['id'],)
    ).fetchall()

    return render_template(
        'staff_dashboard.html',
        stats=stats,
        complaints=dept_complaints,
        notifications=notifications,
        department_name=staff['department_name'] or 'Unassigned'
    )


@app.route('/staff/complaints')
@role_required('staff')
def staff_complaints():
    """List complaints assigned to staff's department."""
    db = get_db()
    staff = g.user
    dept_id = staff['department_id']

    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()
    only_mine = request.args.get('mine', '').strip()

    sql = """
        SELECT c.*, u.full_name AS student_name, u.email AS student_email,
               staff.full_name AS assigned_staff_name, d.name AS department_name
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        LEFT JOIN departments d ON c.department_id = d.id
        WHERE c.department_id = ?
    """
    params = [dept_id]

    if only_mine == '1':
        sql += " AND c.assigned_to = ?"
        params.append(staff['id'])

    if status_filter:
        sql += " AND c.status = ?"
        params.append(status_filter)

    if category_filter:
        sql += " AND c.category = ?"
        params.append(category_filter)

    if search_query:
        sql += " AND (c.ticket_id LIKE ? OR c.title LIKE ? OR u.full_name LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    sql += " ORDER BY c.created_at DESC"
    complaints = db.execute(sql, params).fetchall() if dept_id else []

    return render_template(
        'complaints.html',
        complaints=complaints,
        status_filter=status_filter,
        category_filter=category_filter,
        search_query=search_query,
        only_mine=only_mine,
        page_title=f"Department Complaints ({staff['department_name'] or 'None'})",
        user_role="staff"
    )


@app.route('/complaints/<int:id>/update-status', methods=['POST'])
@role_required('staff', 'admin')
def update_complaint_status(id):
    """Update complaint status and append resolution comment."""
    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ?", (id,)).fetchone()

    if not complaint:
        abort(404)

    # Permission check: Staff can only update their own department's complaints
    if g.user['role'] == 'staff':
        if complaint['department_id'] != g.user['department_id']:
            flash("You do not have permission to update complaints outside your department.", "danger")
            return redirect(url_for('complaint_details', id=id))

    new_status = request.form.get('status', '').strip()
    comment = request.form.get('comment', '').strip()

    valid_statuses = ['Assigned', 'In Progress', 'Resolved', 'Closed']
    if new_status not in valid_statuses:
        flash("Invalid status selected.", "danger")
        return redirect(url_for('complaint_details', id=id))

    if not comment:
        flash("Please provide resolution remarks or an update note explaining this status change.", "danger")
        return redirect(url_for('complaint_details', id=id))

    # Update complaint
    db.execute(
        "UPDATE complaints SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, id)
    )

    # Insert into timeline history
    db.execute(
        """
        INSERT INTO complaint_updates (complaint_id, user_id, status, comment)
        VALUES (?, ?, ?, ?)
        """,
        (id, g.user['id'], new_status, comment)
    )

    # Notify student
    student_id = complaint['student_id']
    msg = f"Status update on your complaint {complaint['ticket_id']}: Changed to '{new_status}'. Note: {comment}"
    add_notification(db, student_id, id, msg)

    # If resolved, prompt student to leave feedback
    if new_status == 'Resolved':
        add_notification(
            db,
            student_id,
            id,
            f"Your complaint {complaint['ticket_id']} is resolved! Please take a moment to submit your feedback and rating."
        )

    db.commit()
    flash(f"Complaint {complaint['ticket_id']} status updated to '{new_status}' successfully.", "success")
    return redirect(url_for('complaint_details', id=id))


# ============================================================================
# Admin Module Routes
# ============================================================================

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    """Admin Dashboard: college-wide metrics, department resolution rates, recent complaints."""
    db = get_db()

    # Metric counts
    stats = {
        'total': db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],
        'pending': db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'").fetchone()[0],
        'assigned': db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Assigned'").fetchone()[0],
        'in_progress': db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0],
        'resolved': db.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')").fetchone()[0],
        'users_count': db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'feedback_count': db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0],
    }

    avg_rating_row = db.execute("SELECT AVG(rating) FROM feedback").fetchone()[0]
    stats['avg_rating'] = round(avg_rating_row, 1) if avg_rating_row else 0.0

    # Department breakdown
    departments_summary = db.execute(
        """
        SELECT d.id, d.name, d.code,
               COUNT(c.id) AS total_complaints,
               SUM(CASE WHEN c.status = 'Pending' THEN 1 ELSE 0 END) AS pending_count,
               SUM(CASE WHEN c.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
               SUM(CASE WHEN c.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS resolved_count
        FROM departments d
        LEFT JOIN complaints c ON d.id = c.department_id
        GROUP BY d.id
        ORDER BY total_complaints DESC
        """
    ).fetchall()

    # Recent complaints
    recent_complaints = db.execute(
        """
        SELECT c.*, u.full_name AS student_name, d.name AS department_name,
               staff.full_name AS assigned_staff_name
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN departments d ON c.department_id = d.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        ORDER BY c.created_at DESC
        LIMIT 6
        """
    ).fetchall()

    # Recent feedback
    recent_feedback = db.execute(
        """
        SELECT f.*, c.ticket_id, c.title AS complaint_title, u.full_name AS student_name
        FROM feedback f
        JOIN complaints c ON f.complaint_id = c.id
        JOIN users u ON f.student_id = u.id
        ORDER BY f.created_at DESC
        LIMIT 4
        """
    ).fetchall()

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        departments_summary=departments_summary,
        recent_complaints=recent_complaints,
        recent_feedback=recent_feedback
    )


@app.route('/admin/complaints')
@role_required('admin')
def admin_complaints():
    """Admin view of all complaints across the institution with filters."""
    db = get_db()

    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    department_filter = request.args.get('department', '').strip()
    search_query = request.args.get('search', '').strip()

    sql = """
        SELECT c.*, u.full_name AS student_name, u.email AS student_email,
               d.name AS department_name, staff.full_name AS assigned_staff_name,
               f.id AS feedback_id, f.rating AS feedback_rating
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN departments d ON c.department_id = d.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        LEFT JOIN feedback f ON c.id = f.complaint_id
        WHERE 1=1
    """
    params = []

    if status_filter:
        sql += " AND c.status = ?"
        params.append(status_filter)

    if category_filter:
        sql += " AND c.category = ?"
        params.append(category_filter)

    if department_filter:
        sql += " AND c.department_id = ?"
        params.append(department_filter)

    if search_query:
        sql += " AND (c.ticket_id LIKE ? OR c.title LIKE ? OR u.full_name LIKE ? OR c.location LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    sql += " ORDER BY c.created_at DESC"
    complaints = db.execute(sql, params).fetchall()

    departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()

    return render_template(
        'complaints.html',
        complaints=complaints,
        departments=departments,
        status_filter=status_filter,
        category_filter=category_filter,
        department_filter=department_filter,
        search_query=search_query,
        page_title="All College Complaints",
        user_role="admin"
    )


@app.route('/complaints/<int:id>/assign', methods=['POST'])
@role_required('admin')
def assign_complaint(id):
    """Admin route to assign a complaint to a department and specific staff member."""
    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ?", (id,)).fetchone()
    if not complaint:
        abort(404)

    department_id = request.form.get('department_id')
    staff_id = request.form.get('assigned_to')
    remarks = request.form.get('remarks', '').strip()

    # Normalize empty values to None
    department_id = int(department_id) if department_id and department_id.isdigit() else None
    staff_id = int(staff_id) if staff_id and staff_id.isdigit() else None

    # Fetch department name & staff name for logging
    dept_name = "Unassigned"
    if department_id:
        d = db.execute("SELECT name FROM departments WHERE id = ?", (department_id,)).fetchone()
        if d:
            dept_name = d['name']

    staff_name = "Department Pool"
    if staff_id:
        s = db.execute("SELECT full_name FROM users WHERE id = ?", (staff_id,)).fetchone()
        if s:
            staff_name = s['full_name']

    # Update status to Assigned if currently Pending
    new_status = 'Assigned' if complaint['status'] == 'Pending' else complaint['status']

    db.execute(
        """
        UPDATE complaints
        SET department_id = ?, assigned_to = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (department_id, staff_id, new_status, id)
    )

    assignment_note = f"Complaint assigned to {dept_name} (Staff: {staff_name})."
    if remarks:
        assignment_note += f" Remarks: {remarks}"

    db.execute(
        """
        INSERT INTO complaint_updates (complaint_id, user_id, status, comment)
        VALUES (?, ?, ?, ?)
        """,
        (id, g.user['id'], new_status, assignment_note)
    )

    # Notify student
    add_notification(
        db,
        complaint['student_id'],
        id,
        f"Your complaint {complaint['ticket_id']} has been assigned to {dept_name}."
    )

    # Notify assigned staff member if assigned
    if staff_id:
        add_notification(
            db,
            staff_id,
            id,
            f"Complaint {complaint['ticket_id']} ({complaint['category']}) has been assigned to you."
        )

    db.commit()
    flash(f"Complaint {complaint['ticket_id']} assigned successfully to {dept_name}.", "success")
    return redirect(url_for('complaint_details', id=id))


@app.route('/admin/users')
@role_required('admin')
def admin_users():
    """Admin view of all registered users with role and department filters."""
    db = get_db()
    role_filter = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip()

    sql = """
        SELECT u.*, d.name AS department_name
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        WHERE 1=1
    """
    params = []

    if role_filter:
        sql += " AND u.role = ?"
        params.append(role_filter)

    if search:
        sql += " AND (u.username LIKE ? OR u.full_name LIKE ? OR u.email LIKE ? OR u.roll_number LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    sql += " ORDER BY u.role, u.full_name"
    users = db.execute(sql, params).fetchall()

    return render_template('users.html', users=users, role_filter=role_filter, search=search)


@app.route('/admin/reports')
@role_required('admin')
def admin_reports():
    """Admin basic reports and metrics."""
    db = get_db()

    total = db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'").fetchone()[0]
    assigned = db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Assigned'").fetchone()[0]
    in_progress = db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')").fetchone()[0]

    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0.0

    # Category statistics
    category_stats = db.execute(
        """
        SELECT category, COUNT(*) as count,
               SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved_count
        FROM complaints
        GROUP BY category
        ORDER BY count DESC
        """
    ).fetchall()

    # Department statistics
    dept_stats = db.execute(
        """
        SELECT d.name, COUNT(c.id) as total,
               SUM(CASE WHEN c.status = 'Pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN c.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
               SUM(CASE WHEN c.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved
        FROM departments d
        LEFT JOIN complaints c ON d.id = c.department_id
        GROUP BY d.id
        ORDER BY total DESC
        """
    ).fetchall()

    # Feedback ratings breakdown
    rating_breakdown = db.execute(
        """
        SELECT rating, COUNT(*) as count
        FROM feedback
        GROUP BY rating
        ORDER BY rating DESC
        """
    ).fetchall()

    return render_template(
        'reports.html',
        total=total,
        pending=pending,
        assigned=assigned,
        in_progress=in_progress,
        resolved=resolved,
        resolution_rate=resolution_rate,
        category_stats=category_stats,
        dept_stats=dept_stats,
        rating_breakdown=rating_breakdown
    )


# ============================================================================
# Universal Complaint Details & Feedback Routes
# ============================================================================

@app.route('/complaints/<int:id>')
@login_required
def complaint_details(id):
    """
    View complete complaint details, activity history, and role-based action controls.
    Enforces authorization:
    - Student: can only view their own complaint.
    - Staff: can only view complaints assigned to their department.
    - Admin: can view any complaint.
    """
    db = get_db()
    complaint = db.execute(
        """
        SELECT c.*,
               u.full_name AS student_name, u.email AS student_email, u.phone AS student_phone, u.roll_number AS student_roll,
               d.name AS department_name, d.id AS dept_id,
               staff.full_name AS assigned_staff_name, staff.email AS assigned_staff_email,
               f.id AS feedback_id, f.rating AS feedback_rating, f.comments AS feedback_comments, f.created_at AS feedback_created_at
        FROM complaints c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN departments d ON c.department_id = d.id
        LEFT JOIN users staff ON c.assigned_to = staff.id
        LEFT JOIN feedback f ON c.id = f.complaint_id
        WHERE c.id = ?
        """,
        (id,)
    ).fetchone()

    if not complaint:
        abort(404)

    # Role-based authorization check
    if g.user['role'] == 'student' and complaint['student_id'] != g.user['id']:
        flash("You are not authorized to view this complaint.", "danger")
        return redirect(url_for('student_dashboard'))

    if g.user['role'] == 'staff' and complaint['department_id'] != g.user['department_id']:
        flash("You are not authorized to view complaints outside your department.", "danger")
        return redirect(url_for('staff_dashboard'))

    # Fetch chronological updates timeline
    updates = db.execute(
        """
        SELECT cu.*, u.full_name AS author_name, u.role AS author_role
        FROM complaint_updates cu
        JOIN users u ON cu.user_id = u.id
        WHERE cu.complaint_id = ?
        ORDER BY cu.created_at ASC
        """,
        (id,)
    ).fetchall()

    # For Admin assignment modal: list departments and available staff members
    departments = []
    staff_members = []
    if g.user['role'] == 'admin':
        departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
        staff_members = db.execute(
            """
            SELECT u.id, u.full_name, u.department_id, d.name AS department_name
            FROM users u
            JOIN departments d ON u.department_id = d.id
            WHERE u.role = 'staff'
            ORDER BY d.name, u.full_name
            """
        ).fetchall()

    return render_template(
        'complaint_details.html',
        complaint=complaint,
        updates=updates,
        departments=departments,
        staff_members=staff_members
    )


@app.route('/complaints/<int:id>/feedback', methods=['GET', 'POST'])
@role_required('student')
def submit_feedback(id):
    """Submit student feedback and 1-5 star rating. Only allowed for Resolved complaints."""
    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ?", (id,)).fetchone()

    if not complaint:
        abort(404)

    # Check ownership
    if complaint['student_id'] != g.user['id']:
        flash("You can only submit feedback for your own complaints.", "danger")
        return redirect(url_for('student_dashboard'))

    # Check status: Feedback only permitted if complaint is resolved
    if complaint['status'] not in ('Resolved', 'Closed'):
        flash("Feedback can only be submitted after the complaint has been marked as Resolved.", "warning")
        return redirect(url_for('complaint_details', id=id))

    # Check if feedback already submitted
    existing = db.execute("SELECT * FROM feedback WHERE complaint_id = ?", (id,)).fetchone()
    if existing:
        flash("Feedback has already been submitted for this complaint.", "info")
        return redirect(url_for('complaint_details', id=id))

    if request.method == 'POST':
        rating_val = request.form.get('rating', '').strip()
        comments = request.form.get('comments', '').strip()

        if not rating_val or not rating_val.isdigit() or not (1 <= int(rating_val) <= 5):
            flash("Please choose a rating between 1 and 5 stars.", "danger")
            return render_template('feedback.html', complaint=complaint)

        rating = int(rating_val)

        # Insert feedback
        db.execute(
            """
            INSERT INTO feedback (complaint_id, student_id, rating, comments)
            VALUES (?, ?, ?, ?)
            """,
            (id, g.user['id'], rating, comments)
        )

        # Log to complaint updates timeline
        db.execute(
            """
            INSERT INTO complaint_updates (complaint_id, user_id, status, comment)
            VALUES (?, ?, ?, ?)
            """,
            (id, g.user['id'], complaint['status'], f"Student submitted {rating}-Star rating & feedback.")
        )

        # Notify assigned staff member if present
        if complaint['assigned_to']:
            add_notification(
                db,
                complaint['assigned_to'],
                id,
                f"Student submitted {rating}-star feedback for complaint {complaint['ticket_id']}."
            )

        db.commit()
        flash("Thank you for your valuable feedback!", "success")
        return redirect(url_for('complaint_details', id=id))

    return render_template('feedback.html', complaint=complaint)


# ============================================================================
# Notifications Center
# ============================================================================

@app.route('/notifications')
@login_required
def notifications():
    """View all notifications for the current user."""
    db = get_db()
    user_id = g.user['id']

    all_notifications = db.execute(
        """
        SELECT n.*, c.ticket_id
        FROM notifications n
        LEFT JOIN complaints c ON n.complaint_id = c.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    return render_template('notifications.html', notifications=all_notifications)


@app.route('/notifications/<int:id>/read')
@login_required
def mark_notification_read(id):
    """Mark a notification as read and redirect to related complaint ticket."""
    db = get_db()
    notif = db.execute(
        "SELECT * FROM notifications WHERE id = ? AND user_id = ?",
        (id, g.user['id'])
    ).fetchone()

    if notif:
        db.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (id,))
        db.commit()
        if notif['complaint_id']:
            return redirect(url_for('complaint_details', id=notif['complaint_id']))

    return redirect(url_for('notifications'))


@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user."""
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (g.user['id'],))
    db.commit()
    flash("All notifications marked as read.", "info")
    return redirect(url_for('notifications'))


# ============================================================================
# API Helper for dynamic Staff selection in Admin Assign form
# ============================================================================

@app.route('/api/departments/<int:dept_id>/staff')
@role_required('admin')
def get_department_staff(dept_id):
    """Return list of staff members for a specific department."""
    db = get_db()
    staff = db.execute(
        "SELECT id, full_name, email FROM users WHERE role = 'staff' AND department_id = ? ORDER BY full_name",
        (dept_id,)
    ).fetchall()
    return jsonify([dict(row) for row in staff])


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', error_title="404 - Page Not Found",
                           error_msg="The requested page or ticket could not be found."), 404


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('base.html', error_title="403 - Forbidden",
                           error_msg="You do not have permission to access this resource."), 403


@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html', error_title="500 - Internal Server Error",
                           error_msg="An unexpected error occurred. Please try again later."), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Local development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1')
    print(f"Starting College Complaint & Resolution System on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=debug)
