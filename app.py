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
        name TEXT, role TEXT, phone TEXT,
        email TEXT, address TEXT)''')

    # Projects
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, location TEXT,
        client TEXT, start_date TEXT)''')

    # Measurements
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER, duct_no TEXT,
        duct_type TEXT, w1 REAL, h1 REAL,
        w2 REAL, h2 REAL, length REAL,
        offset REAL, degree REAL,
        qty INTEGER, factor REAL,
        area REAL, gauge TEXT)''')

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES PART 1 ----------

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# ---------- AUTH ----------

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

@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO employees (name, role, phone, email, address) VALUES (?, ?, ?, ?, ?)',
                  (name, role, phone, email, address))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('employee_registration.html')

@app.route('/vendor_registration', methods=['GET', 'POST'])
def vendor_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        gst = request.form['gst']
        pan = request.form['pan']
        bank_name = request.form['bank_name']
        branch = request.form['branch']
        account_no = request.form['account_no']
        ifsc = request.form['ifsc']
        address = request.form['address']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (name, gst, pan, bank_name, branch, account_no, ifsc, address)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (name, gst, pan, bank_name, branch, account_no, ifsc, address))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('vendor_registration.html')


# ---------- PROJECT & MEASUREMENT ----------

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
        project_id = request.form['project_id']
        duct_no = request.form['duct_no']
        duct_type = request.form['duct_type']
        w1 = float(request.form['w1'])
        h1 = float(request.form['h1'])
        w2 = float(request.form.get('w2', 0) or 0)
        h2 = float(request.form.get('h2', 0) or 0)
        length = float(request.form['length'])
        degree = float(request.form.get('degree', 0) or 0)
        qty = int(request.form['qty'])
        factor = float(request.form.get('factor', 1) or 1)
        gauge = request.form['gauge']

        # ✅ EXACT AREA FORMULAS:
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
                  (project_id, duct_no, duct_type, w1, h1, w2, h2, length, degree, qty, factor, area, gauge))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('measurement_sheet.html', projects=projects)


# ---------- PRODUCTION SUMMARY & PROGRESS ----------

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

@app.route('/enquiry_progress')
def enquiry_progress():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_progress.html')

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

# ---------- RUN APP ----------

if __name__ == '__main__':
    app.run(debug=True)
    
