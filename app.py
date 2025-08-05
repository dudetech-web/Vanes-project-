from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3, hashlib, os

app = Flask(__name__)
app.secret_key = 'secret_key'
DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT)''')

    # Vendors table
    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_name TEXT, gst TEXT, pan TEXT,
        bank_name TEXT, branch TEXT,
        account_no TEXT, ifsc TEXT,
        address TEXT)''')

    # Projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT, vendor_name TEXT,
        quotation TEXT, gst TEXT, start_date TEXT,
        address TEXT, end_date TEXT, email TEXT,
        project_location TEXT, contact_number TEXT,
        project_incharge TEXT, notes TEXT, drawing TEXT)''')

    conn.commit()
    conn.close()

def insert_permanent_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed = hashlib.sha256('demo123'.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)", ('demo', hashed))
    conn.commit()
    conn.close()

def insert_dummy_vendors():
    vendors = [
        ('Alpha Tech', '27AAQCS1234L1Z9', 'AAQCS1234L', 'ICICI', 'Chennai', '1234567890', 'ICIC0001234', 'Chennai, TN'),
        ('Beta Solutions', '29AABCU6789R1Z1', 'AABCU6789R', 'HDFC', 'Bangalore', '9876543210', 'HDFC0005678', 'Bangalore, KA'),
        ('Gamma Engineers', '33AAACG0001L1Z2', 'AAACG0001L', 'SBI', 'Coimbatore', '1122334455', 'SBIN0001111', 'Coimbatore, TN')
    ]
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for v in vendors:
        c.execute("INSERT OR IGNORE INTO vendors (vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", v)
    conn.commit()
    conn.close()

init_db()
insert_permanent_admin()
insert_dummy_vendors()





# --- LOGIN PAGE ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        passwd = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (uname, passwd))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = uname
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')


# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# --- EMPLOYEE REGISTRATION PAGE ---
@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if 'user' not in session:
        return redirect(url_for('login'))
    # Placeholder only: implement DB save logic if needed
    if request.method == 'POST':
        # Capture employee registration logic here
        return redirect(url_for('dashboard'))
    return render_template('employee_registration.html')


# --- VENDOR REGISTRATION PAGE ---
@app.route('/vendor_registration', methods=['GET', 'POST'])
def vendor_registration():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = (
            request.form['vendor_name'],
            request.form['gst'], request.form['pan'],
            request.form['bank_name'], request.form['branch'],
            request.form['account_no'], request.form['ifsc'],
            request.form['address']
        )
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO vendors (vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
        conn.commit()
        conn.close()
        return redirect(url_for('vendor_registration'))

    return render_template('vendor_registration.html')



# --- GET VENDOR INFO (Auto-fill GST and Address) ---
@app.route('/get_vendor_info', methods=['POST'])
def get_vendor_info():
    vendor_name = request.form['vendor_name']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT gst, address FROM vendors WHERE vendor_name = ?", (vendor_name,))
    vendor = c.fetchone()
    conn.close()
    if vendor:
        return jsonify({'gst': vendor[0], 'address': vendor[1]})
    return jsonify({'gst': '', 'address': ''})


# --- NEW PROJECT PAGE ---
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
            request.form['start_date'], request.form['address'],
            request.form['end_date'], request.form['email'],
            request.form['project_location'], request.form['contact_number'],
            request.form['project_incharge'], request.form['notes']
        )
        # Save uploaded drawing
        drawing_path = ""
        if 'drawing' in request.files:
            file = request.files['drawing']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                drawing_path = filename
        data += (drawing_path,)

        c.execute('''INSERT INTO projects (
            enquiry_id, vendor_name, quotation, gst, start_date, address,
            end_date, email, project_location, contact_number, project_incharge,
            notes, drawing_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()

    c.execute("SELECT * FROM projects")
    projects = c.fetchall()
    c.execute("SELECT vendor_name FROM vendors")
    vendors = c.fetchall()
    conn.close()
    return render_template('new_project.html', projects=projects, vendors=vendors)



# --- ADD MEASUREMENT SHEET PAGE ---
@app.route('/add_measurement_sheet')
def add_measurement_sheet():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('add_measurement_sheet.html')


# --- ENQUIRY SUMMARY PAGE ---
@app.route('/enquiry_summary')
def enquiry_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_summary.html')


# --- ENQUIRY PROGRESS TABLE PAGE ---
@app.route('/enquiry_progress_table')
def enquiry_progress_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_progress_table.html')


# --- PRODUCTION NEW PROJECT PAGE ---
@app.route('/production_new_project')
def production_new_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_new_project.html')


# --- PRODUCTION SUMMARY PAGE ---
@app.route('/production_summary')
def production_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_summary.html')


# --- PRODUCTION PROGRESS TABLE PAGE ---
@app.route('/production_progress_table')
def production_progress_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_progress_table.html')


# --- INSERT DUMMY VENDORS (PERMANENT) ---
def insert_permanent_dummy_vendors():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    dummy_vendors = [
        ('Madhan Fabricators', 'GSTTN001', 'ABCDE1234F', 'ICICI Bank', 'Chennai', '1234567890', 'ICIC0000123', 'Chennai'),
        ('Super Ducting Co.', 'GSTTN002', 'BCDEF2345G', 'SBI', 'Coimbatore', '2345678901', 'SBIN0000456', 'Coimbatore'),
        ('Airflow Systems', 'GSTTN003', 'CDEFG3456H', 'HDFC Bank', 'Madurai', '3456789012', 'HDFC0000789', 'Madurai')
    ]
    for vendor in dummy_vendors:
        c.execute("SELECT 1 FROM vendors WHERE vendor_name = ?", (vendor[0],))
        if not c.fetchone():
            c.execute('''INSERT INTO vendors (
                vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', vendor)
    conn.commit()
    conn.close()


@app.route('/insert_dummy_vendors')
def insert_dummy_vendors():
    insert_permanent_dummy_vendors()
    return "Dummy vendors inserted."


# --- CREATE DEFAULT ADMIN (Optional Setup Route) ---
@app.route('/create_admin')
def create_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed))
    conn.commit()
    conn.close()
    return "Admin user created."


# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    # Vendors table
    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_name TEXT UNIQUE,
        gst TEXT,
        pan TEXT,
        bank_name TEXT,
        branch TEXT,
        account_no TEXT,
        ifsc TEXT,
        address TEXT
    )''')

    # Projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT,
        vendor_name TEXT,
        quotation TEXT,
        gst TEXT,
        start_date TEXT,
        end_date TEXT,
        address TEXT,
        email TEXT,
        project_location TEXT,
        contact_number TEXT,
        project_incharge TEXT,
        notes TEXT,
        drawing_filename TEXT
    )''')

    conn.commit()
    conn.close()


# --- MAIN ENTRY POINT ---
if __name__ == '__main__':
    init_db()  # Ensure tables are created
    insert_permanent_dummy_vendors()  # Ensure dummy vendors are inserted
    app.run(debug=True)
