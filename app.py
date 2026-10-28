import os
import uuid
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import database

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'greencity-community-sdg-reporting-secret-key-2026')

# Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Environmental Issue Categories
VALID_CATEGORIES = [
    "Garbage dumping",
    "Water leakage and water wastage",
    "Air pollution",
    "Plastic waste",
    "Tree cutting and damage to green spaces"
]

# Category mapping to icons and colors
CATEGORY_META = {
    "Garbage dumping": {"icon": "fa-trash-can", "color": "#f59e0b", "sdg": "SDG 11 & 12"},
    "Water leakage and water wastage": {"icon": "fa-faucet-drip", "color": "#0ea5e9", "sdg": "SDG 6 & 11"},
    "Air pollution": {"icon": "fa-smog", "color": "#64748b", "sdg": "SDG 3 & 13"},
    "Plastic waste": {"icon": "fa-recycle", "color": "#10b981", "sdg": "SDG 12 & 14"},
    "Tree cutting and damage to green spaces": {"icon": "fa-tree", "color": "#15803d", "sdg": "SDG 11 & 15"}
}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure database is initialized on startup
database.init_db()
database.seed_db()


# -------------------------------------------------------------
# Authentication & Authorization Helpers
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash("Access restricted. You do not have administrator permissions.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Context processor for global template variables
@app.context_processor
def inject_global_data():
    return {
        'now': datetime.now(),
        'valid_categories': VALID_CATEGORIES,
        'category_meta': CATEGORY_META,
        'current_user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('role')
        } if 'user_id' in session else None
    }


# -------------------------------------------------------------
# Public & Informational Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    """Home page with real statistics, latest reports, SDGs, and issue categories."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Calculate real-time statistics
    cursor.execute("SELECT COUNT(*) AS total FROM reports")
    total_reports = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS resolved FROM reports WHERE status = 'Resolved'")
    resolved_reports = cursor.fetchone()['resolved']

    cursor.execute("SELECT COUNT(*) AS progress FROM reports WHERE status = 'In Progress'")
    progress_reports = cursor.fetchone()['progress']

    cursor.execute("SELECT COUNT(*) AS pending FROM reports WHERE status = 'Pending'")
    pending_reports = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) AS total_users FROM users WHERE role = 'resident'")
    total_citizens = cursor.fetchone()['total_users']

    # Category counts for display
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM reports 
        GROUP BY category
    """)
    cat_counts = {row['category']: row['count'] for row in cursor.fetchall()}

    # Recent 4 verified reports
    cursor.execute("""
        SELECT r.*, u.name as submitter_name 
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        LIMIT 4
    """)
    recent_reports = cursor.fetchall()

    conn.close()

    resolution_rate = round((resolved_reports / total_reports * 100), 1) if total_reports > 0 else 0

    stats = {
        'total': total_reports,
        'resolved': resolved_reports,
        'progress': progress_reports,
        'pending': pending_reports,
        'citizens': total_citizens,
        'resolution_rate': resolution_rate
    }

    return render_template(
        'index.html',
        stats=stats,
        cat_counts=cat_counts,
        recent_reports=recent_reports
    )


# -------------------------------------------------------------
# Report Submission (Resident)
# -------------------------------------------------------------
@app.route('/report', methods=['GET', 'POST'])
@login_required
def report_issue():
    """Report an Environmental Issue page."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        lat_str = request.form.get('latitude', '').strip()
        lng_str = request.form.get('longitude', '').strip()

        # Validation
        errors = []
        if not title or len(title) < 5:
            errors.append("Title must be at least 5 characters long.")
        if category not in VALID_CATEGORIES:
            errors.append("Please select a valid environmental category.")
        if not description or len(description) < 15:
            errors.append("Description must be at least 15 characters long.")
        if not address:
            errors.append("Please provide a street address or descriptive location.")

        # Coordinate parsing with sensible fallback to default city center
        latitude = None
        longitude = None
        if lat_str and lng_str:
            try:
                latitude = float(lat_str)
                longitude = float(lng_str)
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                    errors.append("Coordinates are outside valid geographic range.")
            except ValueError:
                errors.append("Invalid coordinates provided.")
        else:
            # Sensible fallback coordinates (GreenCity downtown center)
            latitude = 40.7128
            longitude = -74.0060

        # Photo handling
        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    unique_name = f"user_{session['user_id']}_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.{ext}"
                    secure_name = secure_filename(unique_name)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
                    file.save(file_path)
                    photo_filename = secure_name
                else:
                    errors.append("Invalid photo format. Allowed formats: PNG, JPG, JPEG, GIF, WEBP.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                'report.html',
                form_data=request.form,
                valid_categories=VALID_CATEGORIES
            )

        # Insert report into database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (
                user_id, title, category, description, address,
                latitude, longitude, photo_filename, status, admin_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', 'Report received and queued for civic assessment.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            session['user_id'], title, category, description,
            address, latitude, longitude, photo_filename
        ))
        conn.commit()
        report_id = cursor.lastrowid
        conn.close()

        flash("Your environmental report has been successfully submitted! Civic authorities have been notified.", "success")
        return redirect(url_for('view_reports'))

    return render_template('report.html', form_data={}, valid_categories=VALID_CATEGORIES)


# -------------------------------------------------------------
# View Environmental Reports
# -------------------------------------------------------------
@app.route('/reports')
def view_reports():
    """Browse public environmental reports with search, filter, and interactive map."""
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_order = request.args.get('sort', 'newest').strip()

    conn = database.get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT r.*, u.name as submitter_name 
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (r.title LIKE ? OR r.description LIKE ? OR r.address LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    if category_filter and category_filter in VALID_CATEGORIES:
        query += " AND r.category = ?"
        params.append(category_filter)

    if status_filter and status_filter in ['Pending', 'In Progress', 'Resolved']:
        query += " AND r.status = ?"
        params.append(status_filter)

    if sort_order == 'oldest':
        query += " ORDER BY r.created_at ASC"
    else:
        query += " ORDER BY r.created_at DESC"

    cursor.execute(query, params)
    reports = cursor.fetchall()

    # Total counts for status tabs
    cursor.execute("SELECT status, COUNT(*) as count FROM reports GROUP BY status")
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as count FROM reports")
    total_count = cursor.fetchone()['count']

    conn.close()

    return render_template(
        'reports.html',
        reports=reports,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        sort_order=sort_order,
        status_counts=status_counts,
        total_count=total_count,
        valid_categories=VALID_CATEGORIES
    )


# -------------------------------------------------------------
# JSON API for Map & Modals
# -------------------------------------------------------------
@app.route('/api/reports')
def api_reports():
    """Returns JSON representation of all reports for Leaflet map markers."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.title, r.category, r.description, r.address,
               r.latitude, r.longitude, r.photo_filename, r.status,
               r.created_at, u.name as submitter_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    reports_data = []
    for row in rows:
        reports_data.append({
            'id': row['id'],
            'title': row['title'],
            'category': row['category'],
            'description': row['description'],
            'address': row['address'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'photo_url': url_for('static', filename='uploads/' + row['photo_filename']) if row['photo_filename'] else None,
            'status': row['status'],
            'created_at': row['created_at'],
            'submitter_name': row['submitter_name']
        })

    return jsonify(reports_data)

@app.route('/api/reports/<int:report_id>')
def api_single_report(report_id):
    """Returns detailed information of a single report for modal view."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, u.name as submitter_name, u.email as submitter_email
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
    """, (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Report not found'}), 404

    data = {
        'id': row['id'],
        'title': row['title'],
        'category': row['category'],
        'description': row['description'],
        'address': row['address'],
        'latitude': row['latitude'],
        'longitude': row['longitude'],
        'photo_url': url_for('static', filename='uploads/' + row['photo_filename']) if row['photo_filename'] else None,
        'status': row['status'],
        'admin_notes': row['admin_notes'] or "No official administrative update yet.",
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'submitter_name': row['submitter_name']
    }
    return jsonify(data)


# -------------------------------------------------------------
# Resident Dashboard
# -------------------------------------------------------------
@app.route('/dashboard')
@login_required
def resident_dashboard():
    """Resident Dashboard displaying their submitted reports and tracking stats."""
    status_filter = request.args.get('status', '').strip()
    conn = database.get_db_connection()
    cursor = conn.cursor()

    user_id = session['user_id']

    # Statistics for the logged-in resident
    cursor.execute("SELECT COUNT(*) AS total FROM reports WHERE user_id = ?", (user_id,))
    my_total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS resolved FROM reports WHERE user_id = ? AND status = 'Resolved'", (user_id,))
    my_resolved = cursor.fetchone()['resolved']

    cursor.execute("SELECT COUNT(*) AS progress FROM reports WHERE user_id = ? AND status = 'In Progress'", (user_id,))
    my_progress = cursor.fetchone()['progress']

    cursor.execute("SELECT COUNT(*) AS pending FROM reports WHERE user_id = ? AND status = 'Pending'", (user_id,))
    my_pending = cursor.fetchone()['pending']

    # Fetch user reports
    query = "SELECT * FROM reports WHERE user_id = ?"
    params = [user_id]

    if status_filter in ['Pending', 'In Progress', 'Resolved']:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    my_reports = cursor.fetchall()

    conn.close()

    user_stats = {
        'total': my_total,
        'resolved': my_resolved,
        'progress': my_progress,
        'pending': my_pending,
        'impact_score': (my_resolved * 25) + (my_total * 10)
    }

    return render_template(
        'dashboard.html',
        reports=my_reports,
        stats=user_stats,
        status_filter=status_filter
    )


# -------------------------------------------------------------
# Admin Dashboard & Controls
# -------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin Dashboard for managing all citizen reports with statistics and status controls."""
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Overall Metrics
    cursor.execute("SELECT COUNT(*) as total FROM reports")
    total_reports = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as pending FROM reports WHERE status = 'Pending'")
    pending_reports = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) as progress FROM reports WHERE status = 'In Progress'")
    progress_reports = cursor.fetchone()['progress']

    cursor.execute("SELECT COUNT(*) as resolved FROM reports WHERE status = 'Resolved'")
    resolved_reports = cursor.fetchone()['resolved']

    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    resolution_rate = round((resolved_reports / total_reports * 100), 1) if total_reports > 0 else 0

    # Build report table query
    query = """
        SELECT r.*, u.name as submitter_name, u.email as submitter_email
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (r.title LIKE ? OR r.address LIKE ? OR u.name LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    if category_filter and category_filter in VALID_CATEGORIES:
        query += " AND r.category = ?"
        params.append(category_filter)

    if status_filter and status_filter in ['Pending', 'In Progress', 'Resolved']:
        query += " AND r.status = ?"
        params.append(status_filter)

    query += " ORDER BY r.created_at DESC"
    cursor.execute(query, params)
    all_reports = cursor.fetchall()

    conn.close()

    metrics = {
        'total': total_reports,
        'pending': pending_reports,
        'progress': progress_reports,
        'resolved': resolved_reports,
        'rate': resolution_rate,
        'citizens': total_users
    }

    return render_template(
        'admin.html',
        reports=all_reports,
        metrics=metrics,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        valid_categories=VALID_CATEGORIES
    )

@app.route('/admin/update-status/<int:report_id>', methods=['POST'])
@admin_required
def admin_update_status(report_id):
    """Update report status and admin notes."""
    new_status = request.form.get('status', '').strip()
    admin_notes = request.form.get('admin_notes', '').strip()

    if new_status not in ['Pending', 'In Progress', 'Resolved']:
        flash("Invalid status selection.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reports
        SET status = ?, admin_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, admin_notes, report_id))
    conn.commit()
    conn.close()

    flash(f"Report #{report_id} status updated to '{new_status}'.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-report/<int:report_id>', methods=['POST'])
@admin_required
def admin_delete_report(report_id):
    """Delete a report permanently (admin only)."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Get photo filename if any
    cursor.execute("SELECT photo_filename FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    if row and row['photo_filename']:
        # Don't delete initial sample files
        if not row['photo_filename'].startswith('sample_'):
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], row['photo_filename'])
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except OSError:
                    pass

    cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()

    flash(f"Report #{report_id} has been permanently deleted.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    """Provides structured data for Chart.js analytics in the admin dashboard."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Category breakdown
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM reports 
        GROUP BY category
    """)
    cat_rows = cursor.fetchall()
    categories_dict = {cat: 0 for cat in VALID_CATEGORIES}
    for row in cat_rows:
        categories_dict[row['category']] = row['count']

    # Status breakdown
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM reports 
        GROUP BY status
    """)
    status_rows = cursor.fetchall()
    status_dict = {'Pending': 0, 'In Progress': 0, 'Resolved': 0}
    for row in status_rows:
        if row['status'] in status_dict:
            status_dict[row['status']] = row['count']

    # Monthly/Daily Activity (last 6 recorded days or entries)
    cursor.execute("""
        SELECT SUBSTR(created_at, 1, 10) as day, COUNT(*) as count
        FROM reports
        GROUP BY day
        ORDER BY day ASC
        LIMIT 7
    """)
    timeline_rows = cursor.fetchall()
    timeline_labels = [row['day'] for row in timeline_rows]
    timeline_counts = [row['count'] for row in timeline_rows]

    conn.close()

    return jsonify({
        'categories': {
            'labels': list(categories_dict.keys()),
            'data': list(categories_dict.values())
        },
        'statuses': {
            'labels': list(status_dict.keys()),
            'data': list(status_dict.values())
        },
        'timeline': {
            'labels': timeline_labels,
            'data': timeline_counts
        }
    })


# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if 'user_id' in session:
        return redirect(url_for('resident_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'resident').strip()

        # Validate role (residents default; allow admin choice for testing/demo)
        if role not in ['resident', 'admin']:
            role = 'resident'

        errors = []
        if not name or len(name) < 2:
            errors.append("Please provide your full name (at least 2 characters).")
        if not email or '@' not in email or '.' not in email:
            errors.append("Please enter a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template('register.html', name=name, email=email, role=role)

        # Check existing user
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash("An account with this email address already exists. Please log in.", "warning")
            return redirect(url_for('login', email=email))

        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (name, email, password_hash, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Auto-login after registration
        session.clear()
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['role'] = role

        flash(f"Welcome to GreenCity, {name}! Your citizen account has been created.", "success")
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('resident_dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page with one-click demo credentials."""
    # Quick demo account logins (for instant testing convenience)
    demo_type = request.args.get('demo')
    if demo_type in ['resident', 'admin']:
        demo_email = 'admin@greencity.org' if demo_type == 'admin' else 'resident@greencity.org'
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (demo_email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = user['role']
            flash(f"Logged in as Demo {user['role'].capitalize()} ({user['name']}).", "success")
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('resident_dashboard'))

    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('resident_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html', email=email)

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = user['role']

            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('resident_dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Clear session and log user out."""
    user_name = session.get('user_name', 'Citizen')
    session.clear()
    flash(f"Goodbye, {user_name}. You have been logged out securely.", "info")
    return redirect(url_for('index'))


# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', not_found=True), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("The uploaded photo exceeds the 16MB file limit. Please upload a smaller photo.", "danger")
    return redirect(request.url)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    print(f"[*] GreenCity Environmental Platform starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
