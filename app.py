from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os, hashlib, psycopg2, math, datetime

app = Flask(__name__)
app.secret_key = 'secret_key'

# --- PostgreSQL DB config ---
DATABASE_URL = "postgresql://duct_vendor_app_user:6F8CX3mCEBU8E4azRCf0s6gdQeWaL9bq@dpg-d243r9qli9vc73ca99ag-a.singapore-postgres.render.com/duct_vendor_app"

# --- DB Connection ---
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- Admin & Vendor Setup ---
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS admin (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id SERIAL PRIMARY KEY,
        vendor_name TEXT, gst TEXT, pan TEXT,
        bank_name TEXT, branch TEXT,
        account_no TEXT, ifsc TEXT,
        address TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        enquiry_id TEXT, vendor_name TEXT,
        quotation TEXT, gst TEXT, start_date TEXT,
        address TEXT, end_date TEXT, email TEXT,
        project_location TEXT, contact_number TEXT,
        project_incharge TEXT, notes TEXT, drawing TEXT,
        drawing_filename TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS measurement_sheets (
        id SERIAL PRIMARY KEY,
        duct_no TEXT, duct_type TEXT,
        w1 FLOAT, h1 FLOAT, w2 FLOAT, h2 FLOAT,
        length_radius FLOAT, degree_offset FLOAT,
        quantity INT, gauge TEXT,
        area FLOAT, g24 FLOAT, g22 FLOAT, g20 FLOAT, g18 FLOAT,
        cleat FLOAT, gasket FLOAT, corner_pieces INT,
        project_id INT)''')

    conn.commit()
    cur.close()
    conn.close()

def insert_admin():
    conn = get_db()
    cur = conn.cursor()
    hashed = hashlib.sha256('demo123'.encode()).hexdigest()
    cur.execute("INSERT INTO admin (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING", ('demo', hashed))
    conn.commit()
    cur.close()
    conn.close()

def insert_dummy_vendors():
    vendors = [
        ('Alpha Tech', '27AAQCS1234L1Z9', 'AAQCS1234L', 'ICICI', 'Chennai', '1234567890', 'ICIC0001234', 'Chennai, TN'),
        ('Beta Solutions', '29AABCU6789R1Z1', 'AABCU6789R', 'HDFC', 'Bangalore', '9876543210', 'HDFC0005678', 'Bangalore, KA'),
        ('Gamma Engineers', '33AAACG0001L1Z2', 'AAACG0001L', 'SBI', 'Coimbatore', '1122334455', 'SBIN0001111', 'Coimbatore, TN')
    ]
    conn = get_db()
    cur = conn.cursor()
    for v in vendors:
        cur.execute("""INSERT INTO vendors 
            (vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (vendor_name) DO NOTHING""", v)
    conn.commit()
    cur.close()
    conn.close()

# --- Init on startup ---
init_db()
insert_admin()
insert_dummy_vendors()



# --- LOGIN ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- VENDOR REGISTRATION ---
@app.route('/vendor_registration', methods=['GET', 'POST'])
def vendor_registration():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = (
            request.form['vendor_name'],
            request.form['gst'],
            request.form['pan'],
            request.form['bank_name'],
            request.form['branch'],
            request.form['account_no'],
            request.form['ifsc'],
            request.form['address']
        )
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO vendors 
            (vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", data)
        conn.commit()
        cur.close()
        conn.close()
        return render_template('vendor_registration.html', success="Vendor added successfully")

    return render_template('vendor_registration.html')

# --- NEW PROJECT PAGE ---
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT vendor_name FROM vendors")
    vendors = cur.fetchall()

    if request.method == 'POST':
        file = request.files['drawing']
        filename = secure_filename(file.filename)
        filepath = os.path.join('static', filename)
        file.save(filepath)

        form_data = (
            request.form['enquiry_id'],
            request.form['vendor_name'],
            request.form['quotation'],
            request.form['gst'],
            request.form['start_date'],
            request.form['address'],
            request.form['end_date'],
            request.form['email'],
            request.form['project_location'],
            request.form['contact_number'],
            request.form['project_incharge'],
            request.form['notes'],
            filename,
            filename
        )

        cur.execute("""INSERT INTO projects 
            (enquiry_id, vendor_name, quotation, gst, start_date, address,
            end_date, email, project_location, contact_number, project_incharge, notes, drawing, drawing_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", form_data)

        conn.commit()
        cur.close()
        conn.close()
        return render_template('new_project.html', vendors=vendors, success="Project added successfully")

    cur.close()
    conn.close()
    return render_template('new_project.html', vendors=vendors)


# --- ENQUIRY SUMMARY PAGE ---
@app.route('/enquiry_summary')
def enquiry_summary():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects")
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('enquiry_summary.html', projects=projects)

# --- ADD MEASUREMENT SHEET PAGE ---
@app.route('/add_measurement_sheet')
def add_measurement_sheet():
    if 'user' not in session:
        return redirect(url_for('login'))

    project_id = request.args.get('project_id')
    if not project_id:
        return redirect(url_for('enquiry_summary'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM measurement_sheets WHERE project_id = %s", (project_id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('add_measurement_sheet.html', items=items, project_id=project_id)

# --- ADD ENTRY TO MEASUREMENT SHEET TABLE ---
@app.route('/add_measurement_entry', methods=['POST'])
def add_measurement_entry():
    data = request.get_json()
    project_id = data['project_id']
    duct_no = data['duct_no']
    duct_type = data['duct_type']
    w1 = float(data['w1'] or 0)
    h1 = float(data['h1'] or 0)
    w2 = float(data['w2'] or 0)
    h2 = float(data['h2'] or 0)
    length_radius = float(data['length_radius'] or 0)
    degree_offset = float(data['degree_offset'] or 0)
    quantity = int(data['quantity'] or 1)
    gauge = data['gauge']

    # Area Calculation Based on Duct Type
    if duct_type == 'ST':
        area = 2 * ((w1 + h1) * length_radius) / 144
    elif duct_type == 'RED':
        area = 2 * ((w1 + h1 + w2 + h2) / 2) * length_radius / 144
    elif duct_type == 'DM':
        area = (w1 * h1) / 144
    elif duct_type == 'OFFSET':
        area = ((w1 + h1) * length_radius * 1.5) / 144
    elif duct_type == 'SHOE':
        area = ((w1 + h1) * length_radius * 1.25) / 144
    elif duct_type == 'VANES':
        area = (w1 * h1) / 144
    elif duct_type == 'ELB':
        area = 2 * ((w1 + h1) * degree_offset * 3.14 / 180 * length_radius) / 144
    else:
        area = 0

    area = round(area * quantity, 2)

    # Gauge values
    g24 = area if gauge == '24G' else 0
    g22 = area if gauge == '22G' else 0
    g20 = area if gauge == '20G' else 0
    g18 = area if gauge == '18G' else 0

    # Cleat per gauge
    cleat = 0
    if gauge == '24G':
        cleat = 0.75 * area
    elif gauge == '22G':
        cleat = 1.25 * area
    elif gauge == '20G':
        cleat = 1.75 * area
    elif gauge == '18G':
        cleat = 2.5 * area

    cleat = round(cleat, 2)

    # Accessories
    gasket = round(0.5 * area, 2)
    corner_pieces = 8 if duct_type != 'DM' else 0

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO measurement_sheets 
        (duct_no, duct_type, w1, h1, w2, h2, length_radius, degree_offset, quantity, gauge, area, 
         g24, g22, g20, g18, cleat, gasket, corner_pieces, project_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (duct_no, duct_type, w1, h1, w2, h2, length_radius, degree_offset, quantity, gauge, area,
         g24, g22, g20, g18, cleat, gasket, corner_pieces, project_id))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify(success=True)



# --- DELETE ENTRY FROM MEASUREMENT SHEET ---
@app.route('/delete_measurement/<int:id>', methods=['POST'])
def delete_measurement(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM measurement_sheets WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(success=True)

# --- EDIT ENTRY (RETURN DATA FOR MODAL OR INLINE EDIT) ---
@app.route('/get_measurement/<int:id>', methods=['GET'])
def get_measurement(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM measurement_sheets WHERE id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        keys = ['id', 'duct_no', 'duct_type', 'w1', 'h1', 'w2', 'h2', 'length_radius', 'degree_offset', 'quantity', 'gauge',
                'area', 'g24', 'g22', 'g20', 'g18', 'cleat', 'gasket', 'corner_pieces', 'project_id']
        return jsonify(dict(zip(keys, row)))
    return jsonify(success=False)

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


# --- ENQUIRY PROGRESS TABLE PAGE ---
@app.route('/enquiry_progress_table')
def enquiry_progress_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_progress_table.html')

# --- DASHBOARD PAGE ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- PostgreSQL DATABASE CONNECTION ---
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = 'postgresql://duct_vendor_app_user:6F8CX3mCEBU8E4azRCf0s6gdQeWaL9bq@dpg-d243r9qli9vc73ca99ag-a.singapore-postgres.render.com/duct_vendor_app'

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# --- RUNNING APP ---
if __name__ == '__main__':
    app.run(debug=True)

