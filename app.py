from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import math
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DB_NAME = 'vanes.db'

# ---------- INITIAL SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL)''')

    # Vendors
    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, gst TEXT, pan TEXT,
        bank_name TEXT, branch TEXT,
        account_no TEXT, ifsc TEXT,
        address TEXT)''')

    # Employees
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, dob TEXT, gender TEXT, marital_status TEXT,
        aadhaar TEXT, pan TEXT, esi TEXT, designation TEXT, location TEXT,
        doj TEXT, employment_type TEXT, bank_name TEXT, branch TEXT,
        account_no TEXT, ifsc TEXT, emergency_name TEXT, emergency_relation TEXT,
        emergency_mobile TEXT, blood_group TEXT, allergies TEXT,
        medical_conditions TEXT, reference_name TEXT, reference_mobile TEXT, reference_relation TEXT
    )''')

    # Projects
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, location TEXT,
        client TEXT, start_date TEXT)''')

    # Measurements
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER, duct_no TEXT, duct_type TEXT,
        w1 REAL, h1 REAL, w2 REAL, h2 REAL,
        length REAL, offset REAL, degree REAL,
        qty INTEGER, factor REAL, area REAL, gauge TEXT)''')

    # Enquiry Progress
    c.execute('''CREATE TABLE IF NOT EXISTS enquiry_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT, vendor TEXT, location TEXT,
        start_date TEXT, end_date TEXT, incharge TEXT,
        stage TEXT, status TEXT, remarks TEXT)''')

    conn.commit()
    conn.close()

init_db()

# ---------- AUTH ----------
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed))
    user = c.fetchone()
    conn.close()
    if user:
        session['user'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html', error='Invalid credentials')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- ADMIN USER CREATION ----------
@app.route('/create_admin')
def create_admin():
    hashed = hashlib.sha256("admin123".encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed))
    conn.commit()
    conn.close()
    return "Admin user created!"

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# ---------- EMPLOYEE ----------
@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = {key: request.form.get(key) for key in request.form}
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO employees (
            name, dob, gender, marital_status, aadhaar, pan, esi,
            designation, location, doj, employment_type,
            bank_name, branch, account_no, ifsc,
            emergency_name, emergency_relation, emergency_mobile,
            blood_group, allergies, medical_conditions,
            reference_name, reference_mobile, reference_relation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        tuple(data.values()))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('employee_registration.html')

# ---------- VENDOR ----------
@app.route('/vendor_registration', methods=['GET', 'POST'])
def vendor_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = {key: request.form.get(key) for key in request.form}
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (name, gst, pan, bank_name, branch, account_no, ifsc, address)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  tuple(data.values()))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('vendor_registration.html')

@app.route('/add_dummy_vendors')
def add_dummy_vendors():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    vendors = [
        ('VendorX', 'GSTX123', 'PANX456', 'Axis Bank', 'Branch1', '1234567890', 'IFSC001', 'Chennai'),
        ('VendorY', 'GSTY123', 'PANY456', 'HDFC Bank', 'Branch2', '0987654321', 'IFSC002', 'Bangalore')
    ]
    c.executemany('''INSERT INTO vendors (name, gst, pan, bank_name, branch, account_no, ifsc, address)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', vendors)
    conn.commit()
    conn.close()
    return "Dummy vendors added!"

# ---------- PROJECT ----------
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        client = request.form['client']
        start_date = request.form['start_date']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO projects (name, location, client, start_date) VALUES (?, ?, ?, ?)',
                  (name, location, client, start_date))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    now = datetime.now()
    return render_template('new_project.html', now=now)

# ---------- MEASUREMENT ----------
@app.route('/measurement_sheet', methods=['GET', 'POST'])
def measurement_sheet():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name FROM projects')
    projects = c.fetchall()

    if request.method == 'POST':
        form = request.form
        w1 = float(form['w1'])
        h1 = float(form['h1'])
        w2 = float(form.get('w2') or 0)
        h2 = float(form.get('h2') or 0)
        length = float(form['length'])
        degree = float(form.get('degree') or 0)
        qty = int(form['qty'])
        factor = float(form.get('factor') or 1)
        gauge = form['gauge']
        duct_type = form['duct_type']

        area = 0
        if duct_type == 'ST':
            area = 2 * (w1 + h1) / 1000 * (length / 1000) * qty
        elif duct_type == 'RED':
            area = (w1 + h1 + w2 + h2) / 1000 * (length / 1000) * qty * factor
        elif duct_type == 'DM':
            area = (w1 * h1) / 1_000_000 * qty
        elif duct_type == 'OFFSET':
            area = (w1 + h1 + w2 + h2) / 1000 * ((length + degree) / 1000) * qty * factor
        elif duct_type == 'SHOE':
            area = (w1 + h1) * 2 / 1000 * (length / 1000) * qty * factor
        elif duct_type == 'VANES':
            area = (w1 / 1000) * (2 * math.pi * (w1 / 1000) / 4) * qty
        elif duct_type == 'ELB':
            area = 2 * (w1 + h1) / 1000 * ((h1 / 2) / 1000 + (length / 1000) * math.pi * (degree / 180)) * qty * factor

        c.execute('''INSERT INTO measurements 
            (project_id, duct_no, duct_type, w1, h1, w2, h2, length, degree, qty, factor, area, gauge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (form['project_id'], form['duct_no'], duct_type, w1, h1, w2, h2, length, degree, qty, factor, area, gauge))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('measurement_sheet.html', projects=projects)

# ---------- ENQUIRY ----------
@app.route('/enquiry_progress')
def enquiry_progress():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM enquiry_progress')
    rows = c.fetchall()
    conn.close()
    return render_template('enquiry_progress_table.html', progress_data=rows)

@app.route('/enquiry_progress_form', methods=['GET', 'POST'])
def enquiry_progress_form():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name FROM vendors')
    vendors = [row[0] for row in c.fetchall()]
    conn.close()

    if request.method == 'POST':
        data = {key: request.form.get(key) for key in request.form}
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO enquiry_progress 
            (enquiry_id, vendor, location, start_date, end_date, incharge, stage, status, remarks) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['enquiry_id'], data['vendor'], data['location'], data['start_date'], data['end_date'],
             data['incharge'], data['stage'], data['status'], data['remarks']))
        conn.commit()
        conn.close()
        return redirect(url_for('enquiry_progress'))
    
    return render_template('enquiry_summary.html', vendors=vendors)

# ---------- PRODUCTION ----------
@app.route('/production_summary')
def production_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM measurements')
    data = c.fetchall()
    conn.close()
    return render_template('production_summary.html', data=data)

@app.route('/production_progress')
def production_progress():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_progress_table.html')

@app.route('/production_project')
def production_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name FROM projects')
    projects = c.fetchall()
    conn.close()
    return render_template('production_new_project.html', projects=projects)

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
