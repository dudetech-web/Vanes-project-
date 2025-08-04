from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

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
                    name TEXT,
                    gst TEXT,
                    pan TEXT,
                    bank_name TEXT,
                    branch TEXT,
                    account_no TEXT,
                    ifsc TEXT,
                    address TEXT)''')

    # Measurement sheet table
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    duct_no TEXT,
                    duct_type TEXT,
                    w1 REAL,
                    h1 REAL,
                    w2 REAL,
                    h2 REAL,
                    length REAL,
                    offset REAL,
                    degree REAL,
                    qty INTEGER,
                    factor REAL,
                    area REAL,
                    gauge TEXT)''')

    conn.commit()
    conn.close()

# Initialize DB
init_db()

# ------------- ROUTES -------------

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


from math import pi

@app.route('/add_vendor', methods=['GET', 'POST'])
def add_vendor():
    if request.method == 'POST':
        data = (
            request.form['name'],
            request.form['gst'],
            request.form['pan'],
            request.form['bank_name'],
            request.form['branch'],
            request.form['account_no'],
            request.form['ifsc'],
            request.form['address']
        )

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (name, gst, pan, bank_name, branch, account_no, ifsc, address)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('vendor_form.html')


def calculate_area(duct_type, w1, h1, w2, h2, length, offset, degree, qty, factor):
    if duct_type == "ST":
        return 2 * (w1 + h1) / 1000 * (length / 1000) * qty
    elif duct_type == "RED":
        return (w1 + h1 + w2 + h2) / 1000 * (length / 1000) * qty * factor
    elif duct_type == "DM":
        return (w1 * h1) / 1000000 * qty
    elif duct_type == "OFFSET":
        return (w1 + h1 + w2 + h2) / 1000 * ((length + degree) / 1000) * qty * factor
    elif duct_type == "SHOE":
        return (w1 + h1) * 2 / 1000 * (length / 1000) * qty * factor
    elif duct_type == "VANES":
        return (w1 / 1000) * (2 * pi * (w1 / 1000) / 4) * qty
    elif duct_type == "ELB":
        return 2 * (w1 + h1) / 1000 * ((h1 / 2) / 1000 + (length / 1000) * pi * (degree / 180)) * qty * factor
    else:
        return 0


@app.route('/add_measurement', methods=['GET', 'POST'])
def add_measurement():
    if request.method == 'POST':
        duct_type = request.form['duct_type']
        w1 = float(request.form.get('w1', 0))
        h1 = float(request.form.get('h1', 0))
        w2 = float(request.form.get('w2', 0))
        h2 = float(request.form.get('h2', 0))
        length = float(request.form.get('length', 0))
        offset = float(request.form.get('offset', 0))
        degree = float(request.form.get('degree', 0))
        qty = int(request.form.get('qty', 1))
        factor = float(request.form.get('factor', 1))
        gauge = request.form.get('gauge', '')

        area = calculate_area(duct_type, w1, h1, w2, h2, length, offset, degree, qty, factor)

        data = (
            request.form['project_id'],
            request.form['duct_no'],
            duct_type,
            w1, h1, w2, h2,
            length, offset, degree,
            qty, factor,
            area,
            gauge
        )

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO measurements (project_id, duct_no, duct_type, w1, h1, w2, h2,
                     length, offset, degree, qty, factor, area, gauge)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('measurement_form.html')


@app.route('/summary')
def summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM measurements")
    data = c.fetchall()
    conn.close()
    return render_template('summary.html', data=data)


@app.route('/signature')
def signature():
    return render_template('signature.html')


@app.route('/enquiry_progress')
def enquiry_progress():
    progress_data = [
        {
            'enquiry_id': 'ENQ001',
            'vendor': 'Vendor A',
            'location': 'Site X',
            'start_date': '2025-07-01',
            'end_date': '2025-08-01',
            'incharge': 'John Doe',
            'stage': 'Drawing',
            'status': 'In Progress',
            'remarks': ''
        },
        {
            'enquiry_id': 'ENQ002',
            'vendor': 'Vendor B',
            'location': 'Site Y',
            'start_date': '2025-06-20',
            'end_date': '2025-07-25',
            'incharge': 'Jane Smith',
            'stage': 'Production',
            'status': 'Completed',
            'remarks': 'Delivered early'
        }
    ]
    return render_template('enquiry_progress.html', progress_data=progress_data)





if __name__ == '__main__':
    app.run(debug=True)
    
