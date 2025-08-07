from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.utils import secure_filename
import psycopg2
import hashlib
import datetime
import math
import os
import xlsxwriter

app = Flask(__name__)
app.secret_key = 'secret_key'


from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# PostgreSQL DB connection
DATABASE_URL = 'postgresql://duct_vendor_app_user:6F8CX3mCEBU8E4azRCf0s6gdQeWaL9bq@dpg-d243r9qli9vc73ca99ag-a.singapore-postgres.render.com/duct_vendor_app'

def get_db():
    return psycopg2.connect(DATABASE_URL)

# --- INIT TABLES ---
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id SERIAL PRIMARY KEY,
            vendor_name TEXT,
            gst TEXT,
            pan TEXT,
            bank_name TEXT,
            branch TEXT,
            account_no TEXT,
            ifsc TEXT,
            address TEXT
        )
    ''')

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'unique_vendor_name'
            ) THEN
                ALTER TABLE vendors ADD CONSTRAINT unique_vendor_name UNIQUE (vendor_name);
            END IF;
        END;
        $$;
    """)

    cur.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            enquiry_id TEXT,
            vendor_name TEXT,
            quotation TEXT,
            gst TEXT,
            start_date TEXT,
            address TEXT,
            end_date TEXT,
            email TEXT,
            project_location TEXT,
            contact_number TEXT,
            project_incharge TEXT,
            notes TEXT,
            drawing TEXT,
            drawing_filename TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS measurement_sheets (
            id SERIAL PRIMARY KEY,
            duct_no TEXT,
            duct_type TEXT,
            w1 REAL,
            h1 REAL,
            w2 REAL,
            h2 REAL,
            length REAL,
            degree REAL,
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
            project_id INTEGER REFERENCES projects(id)
        )
    ''')

    conn.commit()
    cur.close()
    conn.close()

# --- INSERT DUMMY VENDORS ---
def insert_dummy_vendors():
    try:
        conn = get_db()
        cur = conn.cursor()

        dummy_vendors = [
            ('Vendor A', 'GST123', 'PAN123', 'Bank A', 'Branch A', '1234567890', 'IFSC001', 'Address A'),
            ('Vendor B', 'GST456', 'PAN456', 'Bank B', 'Branch B', '2345678901', 'IFSC002', 'Address B'),
            ('Vendor C', 'GST789', 'PAN789', 'Bank C', 'Branch C', '3456789012', 'IFSC003', 'Address C')
        ]

        for v in dummy_vendors:
            cur.execute("""
                INSERT INTO vendors 
                (vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vendor_name) DO NOTHING
            """, v)

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error inserting dummy vendors:", e)

# --- CREATE DEFAULT ADMIN USER ---
@app.route('/create_admin')
def create_admin():
    conn = get_db()
    cur = conn.cursor()

    username = 'admin'
    password = hashlib.sha256('admin123'.encode()).hexdigest()

    cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
    if not cur.fetchone():
        cur.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password))

    conn.commit()
    cur.close()
    conn.close()
    return 'Admin created successfully'

# --- INITIALIZE DB + DUMMY DATA ---
init_db()
insert_dummy_vendors()
# --- LOGIN PAGE ---
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        try:
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
                error = 'Invalid credentials'

        except Exception as e:
            # Print full error to console
            print("Login error:", e)
            error = 'Internal server error. Please try again.'

    return render_template('login.html', error=error)

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# --- DASHBOARD PAGE ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# --- VENDOR REGISTRATION PAGE ---
@app.route('/vendor_registration', methods=['GET', 'POST'])
def vendor_registration():
    if 'user' not in session:
        return redirect(url_for('login'))

    message = ''
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
        try:
            cur.execute("""
                INSERT INTO vendors 
                (vendor_name, gst, pan, bank_name, branch, account_no, ifsc, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, data)
            conn.commit()
            message = 'Vendor registered successfully!'
        except Exception as e:
            conn.rollback()
            message = 'Error: Vendor might already exist.'
        finally:
            cur.close()
            conn.close()

    return render_template('vendor_registration.html', message=message)


# --- NEW PROJECT PAGE ---
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT vendor_name FROM vendors")
    vendors = [row[0] for row in cur.fetchall()]

    message = ''
    if request.method == 'POST':
        data = (
            request.form['project_name'],
            request.form['main_client'],
            request.form['end_client'],
            request.form['vendor'],
            request.form['date']
        )
        cur.execute("""
            INSERT INTO projects 
            (project_name, main_client, end_client, vendor, date)
            VALUES (%s, %s, %s, %s, %s)
        """, data)
        conn.commit()
        message = 'Project created successfully!'

    cur.close()
    conn.close()
    return render_template('new_project.html', vendors=vendors, message=message)


# --- ADD MEASUREMENT SHEET PAGE ---
@app.route('/add_measurement_sheet', methods=['GET', 'POST'])
def add_measurement_sheet():
    if 'user' not in session:
        return redirect(url_for('login'))

    project_id = request.args.get('project_id')
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()
        duct_type = data.get('duct_type', '').upper()
        w1 = float(data.get('w1', 0))
        h1 = float(data.get('h1', 0))
        w2 = float(data.get('w2', 0))
        h2 = float(data.get('h2', 0))
        length = float(data.get('length', 0))
        degree = float(data.get('degree', 0))
        quantity = int(data.get('quantity', 1))
        gauge = data.get('gauge', '')

        # Area Calculation
        area = 0
        if duct_type == "ST":
            area = ((w1 + h1) * 2) * length * quantity / 144
        elif duct_type == "RED":
            area = (((w1 + w2) / 2) + h1) * 2 * length * quantity / 144
        elif duct_type == "DM":
            area = (w1 * h1) * quantity / 144
        elif duct_type == "OFFSET":
            area = ((w1 + h1) * 2) * length * quantity / 144
        elif duct_type == "SHOE":
            area = (w1 * h1) * quantity / 144
        elif duct_type == "VANES":
            area = (w1 * h1) * quantity / 144
        elif duct_type == "ELB":
            area = ((w1 + h1) * 3.14 * degree / 90) * quantity / 144

        area = round(area, 2)

        # Accessory calculations
        g24 = g22 = g20 = g18 = 0
        if gauge == "24G":
            g24 = area
        elif gauge == "22G":
            g22 = area
        elif gauge == "20G":
            g20 = area
        elif gauge == "18G":
            g18 = area

        cleat = round(area * 3.5, 2)
        gasket = round(area * 1.2, 2)
        corner_pieces = 0 if duct_type == "DM" else 8

        cur.execute("""
            INSERT INTO measurement_sheets (
                project_id, duct_no, duct_type, w1, h1, w2, h2, length, degree,
                quantity, area, gauge, g24, g22, g20, g18,
                cleat, gasket, corner_pieces
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            project_id, data['duct_no'], duct_type, w1, h1, w2, h2, length, degree,
            quantity, area, gauge, g24, g22, g20, g18,
            cleat, gasket, corner_pieces
        ))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Data saved successfully!'})

    # GET Request: Fetch project details + existing sheet data
    cur.execute("SELECT project_name FROM projects WHERE id = %s", (project_id,))
    project_name = cur.fetchone()[0] if cur.rowcount else 'Unknown Project'

    cur.execute("SELECT * FROM measurement_sheets WHERE project_id = %s", (project_id,))
    sheets = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    return render_template('measurement_sheet.html', project_name=project_name, project_id=project_id, sheets=sheets, columns=columns)


# --- EDIT MEASUREMENT SHEET ROW ---
@app.route('/edit_measurement_row/<int:row_id>', methods=['POST'])
def edit_measurement_row(row_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    data = request.get_json()
    duct_no = data.get('duct_no')
    duct_type = data.get('duct_type')
    w1 = float(data.get('w1', 0))
    h1 = float(data.get('h1', 0))
    w2 = float(data.get('w2', 0))
    h2 = float(data.get('h2', 0))
    length = float(data.get('length', 0))
    degree = float(data.get('degree', 0))
    quantity = int(data.get('quantity', 1))
    gauge = data.get('gauge')

    # Recalculate area and accessories
    area = 0
    if duct_type == "ST":
        area = ((w1 + h1) * 2) * length * quantity / 144
    elif duct_type == "RED":
        area = (((w1 + w2) / 2) + h1) * 2 * length * quantity / 144
    elif duct_type == "DM":
        area = (w1 * h1) * quantity / 144
    elif duct_type == "OFFSET":
        area = ((w1 + h1) * 2) * length * quantity / 144
    elif duct_type == "SHOE":
        area = (w1 * h1) * quantity / 144
    elif duct_type == "VANES":
        area = (w1 * h1) * quantity / 144
    elif duct_type == "ELB":
        area = ((w1 + h1) * 3.14 * degree / 90) * quantity / 144

    area = round(area, 2)

    g24 = g22 = g20 = g18 = 0
    if gauge == "24G":
        g24 = area
    elif gauge == "22G":
        g22 = area
    elif gauge == "20G":
        g20 = area
    elif gauge == "18G":
        g18 = area

    cleat = round(area * 3.5, 2)
    gasket = round(area * 1.2, 2)
    corner_pieces = 0 if duct_type == "DM" else 8

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE measurement_sheets
        SET duct_no=%s, duct_type=%s, w1=%s, h1=%s, w2=%s, h2=%s, length=%s, degree=%s,
            quantity=%s, area=%s, gauge=%s, g24=%s, g22=%s, g20=%s, g18=%s,
            cleat=%s, gasket=%s, corner_pieces=%s
        WHERE id=%s
    """, (
        duct_no, duct_type, w1, h1, w2, h2, length, degree,
        quantity, area, gauge, g24, g22, g20, g18,
        cleat, gasket, corner_pieces, row_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})



@app.route('/dispatch')
def dispatch():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dispatch.html')


# --- DELETE MEASUREMENT ROW ---
@app.route('/delete_measurement_row/<int:row_id>', methods=['POST'])
def delete_measurement_row(row_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM measurement_sheets WHERE id = %s", (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})



@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        marital_status = request.form['marital_status']
        aadhaar = request.form['aadhaar']
        pan = request.form['pan']
        esi = request.form.get('esi')
        designation = request.form['designation']
        location = request.form['location']
        doj = request.form['doj']
        employment_type = request.form['employment_type']
        bank_name = request.form.get('bank_name')
        branch = request.form.get('branch')
        account_no = request.form.get('account_no')
        ifsc = request.form.get('ifsc')
        emergency_name = request.form.get('emergency_name')
        emergency_relation = request.form.get('emergency_relation')
        emergency_mobile = request.form.get('emergency_mobile')
        blood_group = request.form.get('blood_group')
        allergies = request.form.get('allergies')
        medical_conditions = request.form.get('medical_conditions')
        reference_name = request.form.get('reference_name')
        reference_mobile = request.form.get('reference_mobile')
        reference_relation = request.form.get('reference_relation')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO employees (
                name, dob, gender, marital_status, aadhaar, pan, esi,
                designation, location, doj, employment_type,
                bank_name, branch, account_no, ifsc,
                emergency_name, emergency_relation, emergency_mobile,
                blood_group, allergies, medical_conditions,
                reference_name, reference_mobile, reference_relation
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
        """, (
            name, dob, gender, marital_status, aadhaar, pan, esi,
            designation, location, doj, employment_type,
            bank_name, branch, account_no, ifsc,
            emergency_name, emergency_relation, emergency_mobile,
            blood_group, allergies, medical_conditions,
            reference_name, reference_mobile, reference_relation
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('employee_registration.html')


# --- EXPORT TO EXCEL ---
@app.route('/export_measurement_sheet/<int:project_id>')
def export_measurement_sheet(project_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM measurement_sheets WHERE project_id = %s", (project_id,))
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    from io import BytesIO
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet()

    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    for row_idx, row in enumerate(rows, start=1):
        for col_idx, cell in enumerate(row):
            sheet.write(row_idx, col_idx, cell)

    workbook.close()
    output.seek(0)

    return send_file(output, download_name="measurement_sheet.xlsx", as_attachment=True)


# --- OTHER PAGES ---
@app.route('/enquiry_summary')
def enquiry_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_summary.html')


@app.route('/sheet_cutting')
@login_required
def sheet_cutting():
    conn = get_db_connection()
    cur = conn.cursor()

    # Sheet Cutting Data
    cur.execute("SELECT gauge, duct_no, quantity, sheet_cutting FROM sheet_cutting")
    sheet_cutting_data = [dict(gauge=r[0], duct_no=r[1], quantity=r[2], sheet_cutting=r[3]) for r in cur.fetchall()]

    # Fabrication Data
    cur.execute("SELECT gauge, duct_no, quantity, fabrication FROM fabrication")
    fabrication_data = [dict(gauge=r[0], duct_no=r[1], quantity=r[2], fabrication=r[3]) for r in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('sheet_cutting.html',
                           sheet_cutting_data=sheet_cutting_data,
                           fabrication_data=fabrication_data)

@app.route('/enquiry_progress_table')
def enquiry_progress_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_progress.html')

@app.route('/production_new_project')
def production_new_project():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_project.html')

@app.route('/production_summary')
def production_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_summary.html')

@app.route('/production_progress_table')
def production_progress_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('production_progress.html')


@app.route('/fabrication')
def fabrication():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('fabrication.html')



@app.route('/daily_reports')
def daily_reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('daily_reports.html')

@app.route('/weekly_reports')
def weekly_reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('weekly_reports.html')

@app.route('/monthly_reports')
def monthly_reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('monthly_reports.html')


# --- DASHBOARD PAGE ---






# --- APP RUN ---
if __name__ == '__main__':
    with app.app_context():
        create_tables()
        insert_dummy_vendors()
    app.run(debug=True)
