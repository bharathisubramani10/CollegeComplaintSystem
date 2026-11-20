"""
College Complaint & Resolution System - Automated Test Suite
Covers functional test cases for:
1. Authentication & Role-based Authorization
2. Student Module (Submission, tracking, notifications, feedback)
3. Staff Module (Department complaints, status transitions, resolution comments)
4. Admin Module (All complaints, user directory, assignment, reports)
"""

import os
import unittest
import tempfile
from app import app
from database import init_db, get_db


class CollegeComplaintSystemTestCase(unittest.TestCase):
    def setUp(self):
        """Set up a clean temporary SQLite database for each test run."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.environ['COMPLAINTS_DB_PATH'] = self.db_path
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            init_db(self.db_path)

    def tearDown(self):
        """Clean up temporary test database."""
        try:
            os.close(self.db_fd)
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass

    def login(self, username, password):
        """Helper to log in a user."""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        """Helper to log out current user."""
        return self.client.get('/logout', follow_redirects=True)

    # ========================================================================
    # 1. Authentication Tests
    # ========================================================================

    def test_login_success_student(self):
        """Test valid student login."""
        response = self.login('student1', 'student123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Grievance Dashboard', response.data)
        self.assertIn(b'Aarav Sharma', response.data)

    def test_login_success_staff(self):
        """Test valid staff login."""
        response = self.login('staff_it', 'staff123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'IT &amp; Network Support Workspace', response.data)

    def test_login_success_admin(self):
        """Test valid admin login."""
        response = self.login('admin', 'admin123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrative Control Dashboard', response.data)

    def test_login_invalid_credentials(self):
        """Test login with incorrect password."""
        response = self.login('student1', 'wrongpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout(self):
        """Test user logout."""
        self.login('student1', 'student123')
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data)

    # ========================================================================
    # 2. Student Module Tests
    # ========================================================================

    def test_student_submit_complaint(self):
        """Test student submitting a new complaint."""
        self.login('student1', 'student123')
        response = self.client.post('/student/submit-complaint', data=dict(
            category='Wi-Fi',
            title='Slow Internet speed in Library reading room',
            location='Central Library 2nd Floor',
            description='Download speeds are under 50kbps, unable to open IEEE journals.'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'submitted successfully', response.data)
        self.assertIn(b'Slow Internet speed in Library reading room', response.data)

    def test_student_cannot_submit_invalid_category(self):
        """Test validation for invalid complaint category."""
        self.login('student1', 'student123')
        response = self.client.post('/student/submit-complaint', data=dict(
            category='InvalidCategory',
            title='Some issue',
            location='Campus',
            description='Some long description here for testing.'
        ), follow_redirects=True)

        self.assertIn(b'Please select a valid complaint category', response.data)

    def test_student_complaints_isolation(self):
        """Verify student can only access their own complaints, not another student's."""
        # CMP-2026-0002 belongs to student2 (Priya Verma)
        # student1 logs in and tries to access complaint 2
        self.login('student1', 'student123')
        response = self.client.get('/complaints/2', follow_redirects=True)
        self.assertIn(b'You are not authorized to view this complaint', response.data)

    def test_student_feedback_on_resolved_complaint(self):
        """Test student submitting feedback on a resolved complaint."""
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            student1 = db.execute("SELECT id FROM users WHERE username = 'student1'").fetchone()
            cursor.execute(
                """
                INSERT INTO complaints (ticket_id, student_id, category, title, description, location, status)
                VALUES ('CMP-TEST-99', ?, 'Hostel', 'Fan speed regulator fixed', 'Regulator was replaced', 'Room 101', 'Resolved')
                """,
                (student1['id'],)
            )
            db.commit()
            test_id = cursor.lastrowid

        self.login('student1', 'student123')
        # Submit feedback
        response = self.client.post(f'/complaints/{test_id}/feedback', data=dict(
            rating='5',
            comments='Outstanding service! Electrician came within 30 minutes.'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank you for your valuable feedback', response.data)

    def test_student_feedback_blocked_on_unresolved_complaint(self):
        """Verify feedback cannot be submitted on Pending or In-Progress complaints."""
        self.login('student1', 'student123')
        # Complaint 1 is In Progress
        response = self.client.get('/complaints/1/feedback', follow_redirects=True)
        self.assertIn(b'Feedback can only be submitted after the complaint has been marked as Resolved', response.data)

    # ========================================================================
    # 3. Staff Module Tests
    # ========================================================================

    def test_staff_view_department_complaints(self):
        """Test staff viewing complaints for their department."""
        # staff_it belongs to IT & Network Support (id 2)
        self.login('staff_it', 'staff123')
        response = self.client.get('/staff/complaints')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CMP-2026-0001', response.data)  # Wi-Fi complaint

    def test_staff_cannot_access_other_department_complaint(self):
        """Verify staff cannot view or update complaints from other departments."""
        # staff_it (IT) tries to view Complaint 2 (Hostel)
        self.login('staff_it', 'staff123')
        response = self.client.get('/complaints/2', follow_redirects=True)
        self.assertIn(b'You are not authorized to view complaints outside your department', response.data)

    def test_staff_update_status_and_remarks(self):
        """Test staff updating status and adding resolution comments."""
        self.login('staff_it', 'staff123')
        # Update Complaint 1 (Wi-Fi) to Resolved
        response = self.client.post('/complaints/1/update-status', data=dict(
            status='Resolved',
            comment='Replaced damaged PoE cable and verified router connectivity with ping test.'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'status updated to &#39;Resolved&#39; successfully', response.data)

        # Verify timeline was updated
        self.assertIn(b'Replaced damaged PoE cable', response.data)

    # ========================================================================
    # 4. Admin Module Tests
    # ========================================================================

    def test_admin_access_all_complaints(self):
        """Test admin can view all complaints across all departments."""
        self.login('admin', 'admin123')
        response = self.client.get('/admin/complaints')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CMP-2026-0001', response.data)
        self.assertIn(b'CMP-2026-0002', response.data)
        self.assertIn(b'CMP-2026-0003', response.data)

    def test_admin_assign_complaint(self):
        """Test admin assigning a pending complaint to department and staff."""
        self.login('admin', 'admin123')
        # Complaint 4 is currently Pending in Maintenance
        response = self.client.post('/complaints/4/assign', data=dict(
            department_id='3',  # Campus Maintenance
            assigned_to='4',    # Suresh Patel
            remarks='Priority maintenance task for campus laboratory benches.'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'assigned successfully', response.data)

    def test_admin_view_users(self):
        """Test admin viewing the users directory."""
        self.login('admin', 'admin123')
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Aarav Sharma', response.data)
        self.assertIn(b'Rajesh Kumar', response.data)
        self.assertIn(b'Dr. Arvind Swaminathan', response.data)

    def test_admin_view_reports(self):
        """Test admin viewing institutional reports and analytics."""
        self.login('admin', 'admin123')
        response = self.client.get('/admin/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Department Resolution Statistics', response.data)
        self.assertIn(b'Category Distribution', response.data)
        self.assertIn(b'Student Satisfaction Rating Distribution', response.data)

    # ========================================================================
    # 5. Role-Based Access Control Boundaries
    # ========================================================================

    def test_student_cannot_access_admin_dashboard(self):
        """Verify student cannot access admin routes."""
        self.login('student1', 'student123')
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)
        self.assertIn(b'Student Grievance Dashboard', response.data)

    def test_staff_cannot_access_admin_users(self):
        """Verify staff cannot access admin users directory."""
        self.login('staff_it', 'staff123')
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)


if __name__ == '__main__':
    unittest.main()
