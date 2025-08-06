from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import sqlite3, os, hashlib

app = Flask(__name__)
app.secret_key = 'secret_key'
DB_NAME = 'database.db'

# ✅ Helper function to get DB connection
def get_db():
    return sqlite3.connect(DB_NAME)

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
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS measurement_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duct_no TEXT,
            duct_type TEXT,
            w1 REAL,
            h1 REAL,
            w2 REAL,
            h2 REAL,
            length_radius REAL,
            degree_offset REAL,
            quantity INTEGER,
            gauge TEXT,
            area REAL,
            g24 REAL,
            g22 REAL,
            g20 REAL,
            g18 REAL,
            cleat REAL,
            gasket REAL,
            corner_pieces INTEGER,
            project_id INTEGER
        )
    ''')

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

# Ensure 'drawing_filename' column exists in 'projects' table
def ensure_columns():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE projects ADD COLUMN drawing_filename TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

# Initialization
init_db()
ensure_columns()
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



@app.route('/fix_projects_table')
def fix_projects_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE projects ADD COLUMN drawing_filename TEXT")
        msg = "drawing_filename column added successfully."
    except sqlite3.OperationalError:
        msg = "drawing_filename column already exists."
    conn.commit()
    conn.close()
    return msg


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
    from flask import jsonify  # Ensure this is imported at the top

    vendor_name = request.form['vendor_name']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT gst, address FROM vendors WHERE vendor_name = ?", (vendor_name,))
    vendor = c.fetchone()
    conn.close()
    if vendor:
        return jsonify({'gst': vendor[0], 'address': vendor[1]})
    return jsonify({'gst': '', 'address': ''})


# --- NEW PROJECT PAGE --





@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == 'POST':  
        enquiry_id = request.form['enquiry_id']  
        vendor_name = request.form['vendor_name']  
        quotation = request.form['quotation']  
        gst = request.form['gst']  
        start_date = request.form['start_date']  
        address = request.form['address']  
        end_date = request.form['end_date']  
        email = request.form['email']  
        project_location = request.form['project_location']  
        contact_number = request.form['contact_number']  
        project_incharge = request.form['project_incharge']  
        notes = request.form['notes']  
        drawing = request.files['drawing']  

        drawing_filename = None  
        if drawing:  
            drawing_filename = drawing.filename  
            drawing.save(os.path.join('uploads', drawing_filename))  

        c.execute('''  
            INSERT INTO projects (  
                enquiry_id, vendor_name, quotation, gst, start_date, address,  
                end_date, email, project_location, contact_number,  
                project_incharge, notes, drawing_filename  
            )  
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
        ''', (  
            enquiry_id, vendor_name, quotation, gst, start_date, address,  
            end_date, email, project_location, contact_number,  
            project_incharge, notes, drawing_filename  
        ))  
        conn.commit()  

    # Fetch vendors  
    c.execute("SELECT vendor_name FROM vendors")  
    vendors = [{'vendor_name': row[0]} for row in c.fetchall()]  

    # Fetch existing projects  
    c.execute('SELECT * FROM projects')  
    projects = [dict(  
        id=row[0],  # Needed for action buttons
        enquiry_id=row[1], 
        quotation=row[3], 
        start_date=row[5],  
        end_date=row[6], 
        project_location=row[8], 
        project_incharge=row[10],  
        contact_number=row[9], 
        email=row[7], 
        notes=row[11]  
    ) for row in c.fetchall()]  

    conn.close()  
    return render_template('new_project.html', vendors=vendors, projects=projects)
# --- ADD MEASUREMENT SHEET PAGE ---




# Measurement sheet route


@app.route('/add_measurement_sheet', methods=['GET', 'POST'])
def add_measurement_sheet():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        duct_no = request.form['duct_no']
        duct_type = request.form['duct_type'].lower()
        w1 = float(request.form['w1'] or 0)
        h1 = float(request.form['h1'] or 0)
        w2 = float(request.form['w2'] or 0)
        h2 = float(request.form['h2'] or 0)
        length = float(request.form['length'] or 0)
        degree = float(request.form['degree'] or 0)
        quantity = int(request.form['quantity'] or 1)
        factor = float(request.form['factor'] or 1)

        area = 0
        if duct_type == 'st':
            area = 2 * ((w1 + h1) / 1000) * (length / 1000) * quantity
        elif duct_type == 'red':
            area = ((w1 + h1 + w2 + h2) / 2 / 1000) * (length / 1000) * quantity * factor
        elif duct_type == 'dm':
            area = (w1 * h1) / 1000000 * quantity
        elif duct_type == 'offset':
            area = ((w1 + h1 + w2 + h2) / 2 / 1000) * (length / 1000) * quantity * factor
        elif duct_type == 'shoe':
            area = (w1 + h1) / 1000 * (length / 1000) * quantity * factor
        elif duct_type == 'vanes':
            area = (w1 / 1000) * (h1 / 1000) * quantity
        elif duct_type == 'elb':
            area = 2 * ((w1 + h1) / 1000) * ((length * degree / 360) / 1000) * quantity * factor

        # Gauge logic (optional default logic, feel free to modify)
        gauge = '24G'
        if w1 > 1000:
            gauge = '22G'
        if w1 > 1500:
            gauge = '20G'
        if w1 > 2000:
            gauge = '18G'

        # Accessory logic (exactly from your formula sheet)
        cleat_24g = 12 * quantity if gauge == '24G' else 0
        cleat_22g = 10 * quantity if gauge == '22G' else 0
        cleat_20g = 8 * quantity if gauge == '20G' else 0
        cleat_18g = 4 * quantity if gauge == '18G' else 0
        gasket = (w1 + w2 + h1 + h2) * quantity / 1000
        corner_pieces = 8 if duct_type == 'dm' else 0

        # Insert into correct table: measurement_sheets
        c.execute('''
            INSERT INTO measurement_sheets 
            (duct_no, duct_type, w1, h1, w2, h2, length, degree, quantity, factor, area, gauge, 
             cleat_24g, cleat_22g, cleat_20g, cleat_18g, cleat, gasket, corner_pieces)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            duct_no, duct_type, w1, h1, w2, h2, length, degree, quantity, factor, area, gauge,
            cleat_24g, cleat_22g, cleat_20g, cleat_18g, 0, gasket, corner_pieces
        ))
        conn.commit()

    # Use the correct table here as well
    entries = c.execute('SELECT * FROM measurement_sheets').fetchall()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('measurement_sheet.html', entries=entries, timestamp=timestamp)


# Delete route




@app.route('/edit_measurement_sheet/<int:sheet_id>', methods=['GET', 'POST'])
def edit_measurement_sheet(sheet_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == 'POST':
        # Get updated values from form
        duct_no = request.form['duct_no']
        duct_type = request.form['duct_type']
        w1 = float(request.form['w1'])
        h1 = float(request.form['h1'])
        w2 = float(request.form['w2'])
        h2 = float(request.form['h2'])
        length_radius = float(request.form['length_radius'])
        degree_offset = float(request.form['degree_offset'])
        quantity = int(request.form['quantity'])
        gauge = request.form['gauge']

        # Update the row
        c.execute('''
            UPDATE measurement_sheets
            SET duct_no=?, duct_type=?, w1=?, h1=?, w2=?, h2=?, length_radius=?, degree_offset=?, quantity=?, gauge=?
            WHERE id=?
        ''', (duct_no, duct_type, w1, h1, w2, h2, length_radius, degree_offset, quantity, gauge, sheet_id))

        conn.commit()
        conn.close()
        return redirect(url_for('add_measurement_sheet'))

    # GET: load existing data
    c.execute('SELECT * FROM measurement_sheets WHERE id=?', (sheet_id,))
    sheet = c.fetchone()
    conn.close()

    return render_template('edit_measurement_sheet.html', sheet=sheet)


@app.route('/delete_measurement_sheet/<int:sheet_id>')
def delete_measurement_sheet(sheet_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM measurement_sheets WHERE id=?', (sheet_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('measurement_sheet'))

    

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
    return render_template('enquiry_progress.html')


# --- PRODUCTION NEW PROJECT PAGE ---
@app.route('/production_new_project')
def production_new_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_project.html')


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
    return render_template('production_progress.html')


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
