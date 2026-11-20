# College Complaint & Resolution System

A complete, functional, beginner-friendly web application engineered for college campus grievance redressal and resolution management. Built with **Python Flask**, **SQLite**, **Jinja2 Templates**, **CSS3**, and **Vanilla JavaScript**.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Technology Stack](#-technology-stack)
3. [User Roles & Key Features](#-user-roles--key-features)
4. [Database Design & Schema](#-database-design--schema)
5. [Demo Accounts (Quick Evaluation)](#-demo-accounts-quick-evaluation)
6. [Installation & Setup](#-installation--setup)
7. [Running the Application](#-running-the-application)
8. [Testing & Evaluation Guide](#-testing--evaluation-guide)
9. [Project Structure](#-project-structure)
10. [Preparing for GitHub Upload](#-preparing-for-github-upload)

---

## 🎯 Project Overview

In traditional college campuses, students often face delays when reporting infrastructure, hostel, Wi-Fi, and classroom facility issues due to lack of a centralized tracking mechanism.

The **College Complaint & Resolution System** bridges this gap by providing:
- A transparent grievance filing and ticketing pipeline for **Students**.
- A departmental workspace for **Staff** to inspect, update status, and log resolution remarks.
- A central control dashboard for **Administrators** to assign complaints, oversee department resolution times, and analyze student satisfaction ratings.

---

## ⚡ Technology Stack

Strictly lightweight, beginner-friendly, and production-compliant:

| Component | Technology | Description |
|---|---|---|
| **Backend** | Python 3 + Flask | Modular routes, session authentication, and role authorization |
| **Database** | SQLite 3 | Relational database with foreign key integrity and timestamps |
| **Security** | Werkzeug Security | Secure PBKDF2/SHA-256 password hashing |
| **Frontend** | HTML5 + Jinja2 | Semantic templates and dynamic layout inheritance |
| **Styling** | Modern CSS3 | Custom CSS variables, responsive sidebar, stat cards, badges |
| **Client Scripts** | Vanilla JavaScript | Pure JS (no React, jQuery, or Node.js) for search, filters, modals, stars |
| **Version Control**| Git & GitHub | Clean repository structure with `.gitignore` |

---

## 👥 User Roles & Key Features

### 1. Student Module
- **Secure Authentication**: Log in and log out with session persistence.
- **Submit Complaint**: Form supporting categories:
  - `Hostel` (Rooms, plumbing, water, sanitation)
  - `Classroom` (Projectors, smartboards, benches, lighting)
  - `Wi-Fi` (Routers, coverage, login portals, bandwidth)
  - `Maintenance` (Electrical, civil, furniture, carpentry)
  - `Other` (General campus amenities)
- **Unique Ticket ID**: Auto-generates formal ticket codes (e.g., `CMP-2026-0001`).
- **Live Tracking**: Real-time status badges (`Pending`, `Assigned`, `In Progress`, `Resolved`).
- **Chronological Timeline**: View full progress notes logged by technicians and admins.
- **In-App Notifications**: Alerts when tickets are assigned, updated, or resolved.
- **Resolution Feedback & Rating**: Submit an interactive 1–5 star rating and review **only after** a complaint is marked as Resolved.
- **Privacy Enforcement**: Students can strictly only view and track their own complaints.

### 2. Staff Module
- **Departmental Workspace**: Automatically linked to staff member's department (e.g. IT, Hostel, Maintenance).
- **Scoped Complaints**: Staff can strictly view complaints assigned to their department.
- **Status Progression**:
  - `Assigned` (Acknowledged by department)
  - `In Progress` (Technician dispatched / parts ordered)
  - `Resolved` (Issue rectified and tested)
- **Resolution Remarks**: Mandatory remarks field documenting the repair work done.
- **Notifications**: Instant alerts when new tickets are assigned to the department or staff member.

### 3. Admin Module
- **Executive Control Center**: College-wide overview with real-time summary metric cards:
  - Total Complaints
  - Pending Initial Review
  - In Progress
  - Successfully Resolved
  - Total Registered Users
  - Average Student Satisfaction Rating (⭐ 1–5)
- **Master Complaints Directory**: Search and multi-filter complaints across all departments.
- **Assignment System**: Assign or reassign complaints to departments and specific staff members with custom remarks.
- **Department Workload Monitoring**: Real-time department resolution rate progress bars.
- **Users Directory**: Inspect all registered students, staff officers, and administrators.
- **Reports & Analytics**: Visual summary tables for category distribution, department turnaround, and star rating metrics.

---

## 🗄️ Database Design & Schema

The database utilizes SQLite with `PRAGMA foreign_keys = ON;` and includes 6 interconnected tables:

```
+---------------+        +-------------------+
|  departments  |<-------|       users       |
+---------------+        +-------------------+
        ^                  ^       ^       ^
        |                  |       |       |
        +------+-----------+       |       |
               |                   |       |
      +-----------------+          |       |
      |   complaints    |----------+       |
      +-----------------+                  |
        |             |                    |
        v             v                    |
+----------------+  +-----------------+    |
|complaint_update|  |    feedback     |----+
+----------------+  +-----------------+
        |
        v
+----------------+
| notifications  |
+----------------+
```

### Table Specifications:
1. `users`: Stores user credentials (`password_hash`), full name, email, role (`student`, `staff`, `admin`), phone, roll number, and department foreign key.
2. `departments`: College departments (`Hostel Administration`, `IT & Network Support`, `Campus Maintenance`, `Academic Facilities`, `General Administration`).
3. `complaints`: Master grievance table with `ticket_id`, `student_id`, `category`, `title`, `description`, `location`, `department_id`, `assigned_to`, `status`, `created_at`, `updated_at`.
4. `complaint_updates`: Audit log storing timestamped progress notes, author `user_id`, and status transitions.
5. `feedback`: 1-to-1 relationship with resolved complaints; stores `rating` (1–5) and student `comments`.
6. `notifications`: In-app notification queue with `is_read` flag for updates.

---

## 🔑 Demo Accounts (Quick Evaluation)

The application automatically seeds realistic demo data and accounts upon first run.

> **Tip**: The login screen features **One-Click Demo Fill buttons** for effortless testing!

| Role | Username | Password | Full Name / Title | Department / Roll No |
|---|---|---|---|---|
| **Admin** | `admin` | `admin123` | Dr. Arvind Swaminathan (Dean) | Central Administration |
| **Staff (IT)** | `staff_it` | `staff123` | Anil Sharma (Network Engineer) | IT & Network Support |
| **Staff (Hostel)** | `staff_hostel` | `staff123` | Rajesh Kumar (Hostel Warden) | Hostel Administration |
| **Staff (Maintenance)** | `staff_maint` | `staff123` | Suresh Patel (Maintenance Lead) | Campus Maintenance |
| **Student 1** | `student1` | `student123` | Aarav Sharma | Roll: `2024CS101` |
| **Student 2** | `student2` | `student123` | Priya Verma | Roll: `2024EC204` |
| **Student 3** | `student3` | `student123` | Rohan Gupta | Roll: `2024ME312` |

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher installed on your system.

### 1. Clone or Open the Project Directory
```bash
cd CollegeComplaintSystem
```

### 2. Create and Activate a Virtual Environment (Recommended)
On Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```

On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Application

### Option A: Standard Run
Run the application using:
```bash
python app.py
```

### Option B: From the Workspace Root
If you are in the parent directory, you can also run:
```bash
python app.py
```

### Accessing the Web Application
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
The database (`instance/complaints.db`) will be automatically created and populated if it does not already exist.

---

## 🧪 Testing & Evaluation Guide

### Automated Test Suite
To run the automated test suite covering all functional and authorization test cases:
```bash
python -m unittest test_app.py
```
*Expected Result: 19 tests run with status `OK`.*

### Manual Step-by-Step Test Scenarios

#### Scenario 1: Student Files a Complaint
1. Open `http://127.0.0.1:5000/login`.
2. Click the **"👤 Student"** quick fill button (or enter `student1` / `student123`) and click **Sign In**.
3. Click **"➕ File Complaint"** in the sidebar.
4. Select Category: `Wi-Fi`.
5. Enter Location: `Hostel Block B, Room 305`.
6. Enter Title: `Severe packet loss and intermittent Wi-Fi drops`.
7. Enter Description: `The Wi-Fi disconnects every 5 minutes while attending online lab sessions.`
8. Click **Submit Complaint**.
9. Notice the generated Ticket ID (e.g. `CMP-2026-0006`), initial status badge `Pending`, and the timeline event.

#### Scenario 2: Admin Assigns the Complaint
1. Log out and sign in as **Admin** (`admin` / `admin123`).
2. Notice the new pending complaint on the **Administrative Control Dashboard**.
3. Click on the ticket or navigate to **"📑 All Complaints"**.
4. Open the ticket and click **"📌 Assign Dept / Staff"**.
5. Select Department: `IT & Network Support`.
6. Select Staff: `Anil Sharma`.
7. Add Remark: `Please inspect the switch and channel interference.`
8. Click **Confirm Assignment**.
9. The status automatically transitions to `Assigned` and logs in the timeline.

#### Scenario 3: Staff Updates Status with Resolution Remarks
1. Log out and sign in as **Staff** (`staff_it` / `staff123`).
2. On the **Staff Workspace**, locate the assigned ticket.
3. Click **"Inspect & Update"**.
4. Click **"🔄 Update Status"**.
5. Change Status to `In Progress` and add remark: `Resetting 5GHz AP channel configuration.` Click **Save**.
6. When work is completed, click **"🔄 Update Status"** again, select `Resolved`, and add remark: `Router channel shifted to Channel 36. Speed test shows stable 100Mbps.` Click **Save**.

#### Scenario 4: Student Feedback Submission
1. Log out and sign back in as **Student** (`student1` / `student123`).
2. Notice the notification bell with the new alert: *"Your complaint has been marked as Resolved"*.
3. Open the ticket details. Notice the prominent **"⭐ Submit Feedback"** button.
4. Click **Submit Feedback**.
5. Select **5 Stars** (notice the live star hover and description).
6. Enter Comment: `Very quick turnaround, Wi-Fi works flawlessly now!`
7. Click **Submit Feedback**. The review is permanently added to the ticket history.

#### Scenario 5: Security & Isolation Verification
1. Try accessing another student's complaint directly via URL (e.g., student1 accessing `/complaints/2`).
   - *Result*: Access is blocked with an alert: *"You are not authorized to view this complaint"*.
2. Try accessing Admin routes as a student (e.g. `/admin/dashboard` or `/admin/users`).
   - *Result*: Access is blocked with an alert: *"Access denied"*.
3. Try submitting feedback on an un-resolved complaint (e.g. a Pending complaint).
   - *Result*: Access is blocked with: *"Feedback can only be submitted after the complaint has been marked as Resolved"*.

---

## 📁 Project Structure

```
CollegeComplaintSystem/
├── app.py                     # Main Flask application and route handlers
├── database.py                # Database connection, init_db, and sample data seeding
├── requirements.txt           # Python dependency requirements
├── README.md                  # Comprehensive documentation and evaluation guide
├── schema.sql                 # SQLite relational database schema
├── test_app.py                # Automated unittest suite (19 unit/functional test cases)
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base layout with sidebar, topbar, alerts, and navigation
│   ├── login.html             # Login screen with 1-click demo account autofill
│   ├── student_dashboard.html # Student statistics, recent tickets, and alerts
│   ├── staff_dashboard.html   # Staff department workspace, queue, and notifications
│   ├── admin_dashboard.html   # Administrator command center and metrics
│   ├── submit_complaint.html  # Complaint submission form with validation
│   ├── complaints.html        # Scoped complaints data table with search and filters
│   ├── complaint_details.html # Ticket details, timeline, staff updates & assignment
│   ├── feedback.html          # Star rating and feedback submission form
│   ├── users.html             # Admin user accounts directory
│   ├── reports.html           # Institutional reports and resolution analytics
│   └── notifications.html     # Notifications center with ticket shortcuts
├── static/
│   ├── css/
│   │   └── style.css          # Responsive styling, color themes, badges, cards
│   └── js/
│       └── script.js          # Vanilla JS for search, filters, modals, stars, autofill
└── instance/
    └── complaints.db          # Auto-created SQLite database file
```

---

## 📦 Preparing for GitHub Upload

The repository is fully configured for Git:
1. Initialize repository (if not already done):
   ```bash
   git init
   ```
2. Check status and stage all files:
   ```bash
   git add .
   ```
3. Create your initial commit:
   ```bash
   git commit -m "feat: complete College Complaint & Resolution System"
   ```
4. Push to your GitHub repository:
   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```

---

## 🎓 Academic Mini-Project Suitability
This project was designed with clean, readable code and clear separation of concerns (MVC architecture), making it an ideal demonstration project for college examinations, technical vivas, and software engineering coursework.
