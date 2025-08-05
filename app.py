from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_NAME = 'database.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT, password TEXT)''')

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
                    name TEXT, email TEXT, contact TEXT,
                    designation TEXT, department TEXT,
                    address TEXT)''')

    # Projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enquiry_id TEXT, vendor_name TEXT,
                    quotation TEXT, gst TEXT, start_date TEXT,
                    end_date TEXT, address TEXT,
                    email TEXT, project_location TEXT,
                    contact_number TEXT, drawing TEXT,
                    project_incharge TEXT, notes TEXT)''')

    conn.commit()
    conn.close()

init_db()

# Route: Create Admin User
@app.route('/create_admin')
def create_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password))
    conn.commit()
    conn.close()
    return 'Admin user created'

# Route: Dummy Login
@app.route('/dummy_login')
def dummy_login():
    session['user'] = 'demo'
    return redirect(url_for('dashboard'))

# Route: Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (uname, pwd))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = uname
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

# Route: Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Route: Vendor Registration
@app.route('/vendor_registration', methods=['GET', 'POST'])
def vendor_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = (
            request.form['name'], request.form['gst'], request.form['pan'],
            request.form['bank_name'], request.form['branch'],
            request.form['account_no'], request.form['ifsc'],
            request.form['address']
        )
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (name, gst, pan, bank_name, branch, account_no, ifsc, address)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('vendor_registration.html')

# Route: Employee Registration
@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = (
            request.form['name'], request.form['email'], request.form['contact'],
            request.form['designation'], request.form['department'],
            request.form['address']
        )
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO employees (name, email, contact, designation, department, address)
                     VALUES (?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('employee_registration.html')

# Route: Insert Dummy Vendors
@app.route('/insert_dummy_vendors')
def insert_dummy_vendors():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    vendors = [
        ('Vendor A', 'GST123A', 'PAN123A', 'Bank A', 'Branch A', '11111111', 'IFSC001', 'Address A'),
        ('Vendor B', 'GST123B', 'PAN123B', 'Bank B', 'Branch B', '22222222', 'IFSC002', 'Address B'),
        ('Vendor C', 'GST123C', 'PAN123C', 'Bank C', 'Branch C', '33333333', 'IFSC003', 'Address C')
    ]
    for v in vendors:
        c.execute("INSERT INTO vendors (name, gst, pan, bank_name, branch, account_no, ifsc, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", v)
    conn.commit()
    conn.close()
    return 'Dummy vendors inserted'

# Route: Get Vendor Info for Dropdown Autofill
@app.route('/get_vendor_info', methods=['POST'])
def get_vendor_info():
    vendor_name = request.form['vendor_name']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT gst, address FROM vendors WHERE name = ?", (vendor_name,))
    vendor = c.fetchone()
    conn.close()
    if vendor:
        return jsonify({'gst': vendor[0], 'address': vendor[1]})
    return jsonify({'gst': '', 'address': ''})

# Route: New Project
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == 'POST':
        data = (
            request.form['enquiry_id'], request.form['vendor_name'],
            request.form['quotation'], request.form['gst'],
            request.form['start_date'], request.form['end_date'],
            request.form['address'], request.form['email'],
            request.form['project_location'], request.form['contact_number'],
            '',  # drawing filename placeholder
            request.form['project_incharge'], request.form['notes']
        )
        c.execute('''INSERT INTO projects (enquiry_id, vendor_name, quotation, gst, start_date, end_date,
                                            address, email, project_location, contact_number,
                                            drawing, project_incharge, notes)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()

    # Fetch all vendors and projects for rendering
    c.execute("SELECT name FROM vendors")
    vendors = [{'vendor_name': row[0]} for row in c.fetchall()]

    c.execute("SELECT * FROM projects ORDER BY id DESC")
    projects = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    conn.close()

    return render_template('new_project.html', vendors=vendors, projects=projects)

# Route: Add Measurement Sheet (Placeholder)
@app.route('/add_measurement_sheet')
def add_measurement_sheet():
    return render_template('add_measurement_sheet.html')

# Other Production Pages
@app.route('/production_new_project')
def production_new_project():
    return render_template('production_new_project.html')

@app.route('/production_progress_table')
def production_progress_table():
    return render_template('production_progress_table.html')

@app.route('/production_summary')
def production_summary():
    return render_template('production_summary.html')

@app.route('/enquiry_progress_table')
def enquiry_progress_table():
    return render_template('enquiry_progress_table.html')

@app.route('/enquiry_summary')
def enquiry_summary():
    return render_template('enquiry_summary.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
