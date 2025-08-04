from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DB_NAME = 'vanes.db'

# ---------- INITIAL SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL)''')

    # Vendors table
    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, gst TEXT, pan TEXT,
        bank_name TEXT, branch TEXT,
        account_no TEXT, ifsc TEXT,
        address TEXT)''')

    # Employees table
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        dob TEXT,
        gender TEXT,
        marital_status TEXT,
        aadhaar TEXT,
        pan TEXT,
        esi TEXT,
        designation TEXT,
        location TEXT,
        doj TEXT,
        employment_type TEXT,
        bank_name TEXT,
        branch TEXT,
        account_no TEXT,
        ifsc TEXT,
        emergency_name TEXT,
        emergency_relation TEXT,
        emergency_mobile TEXT,
        blood_group TEXT,
        allergies TEXT,
        medical_conditions TEXT,
        reference_name TEXT,
        reference_mobile TEXT,
        reference_relation TEXT
    )''')

    # Projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, location TEXT,
        client TEXT, start_date TEXT)''')

    # Measurements table
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER, duct_no TEXT,
        duct_type TEXT, w1 REAL, h1 REAL,
        w2 REAL, h2 REAL, length REAL,
        offset REAL, degree REAL,
        qty INTEGER, factor REAL,
        area REAL, gauge TEXT)''')

    # Enquiry Progress table
    c.execute('''CREATE TABLE IF NOT EXISTS enquiry_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT,
        vendor TEXT,
        location TEXT,
        start_date TEXT,
        end_date TEXT,
        incharge TEXT,
        stage TEXT,
        status TEXT,
        remarks TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
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

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

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
    return render_template('enquiry_progress.html', progress_data=rows)

@app.route('/add_dummy_enquiry')
def add_dummy_enquiry():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO enquiry_progress 
        (enquiry_id, vendor, location, start_date, end_date, incharge, stage, status, remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        ('ENQ001', 'VendorX', 'Chennai', '2025-08-01', '2025-08-15', 'John Doe', 'Drawing', 'In Progress', 'Initial design phase'))
    conn.commit()
    conn.close()
    return "Dummy enquiry added!"

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
    return render_template('new_project.html')

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
    return render_template('production_progress.html')

@app.route('/enquiry_summary')
def enquiry_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_summary.html')

@app.route('/production_project')
def production_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name FROM projects')
    projects = c.fetchall()
    conn.close()
    return render_template('production_project.html', projects=projects)

@app.route('/create_admin')
def create_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'password'))
    conn.commit()
    conn.close()
    return "Admin user created!"

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
