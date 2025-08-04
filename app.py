from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import os
import math
import psycopg2
from fpdf import FPDF
import xlsxwriter

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# PostgreSQL connection

conn = psycopg2.connect(
    dbname="duct_vendor_app",
    user="duct_vendor_app_user",
    password="6F8CX3mCEBU8E4azRCf0s6gdQeWaL9bq",
    host="dpg-d243r9qli9vc73ca99ag-a.singapore-postgres.render.com",
    port=5432

)
cur = conn.cursor()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/do_login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    # Dummy credentials for now
    if username == 'admin' and password == 'password':
        session['user'] = username
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# =====================
# Vendor Registration
# =====================
@app.route('/register_vendor', methods=['GET', 'POST'])
def register_vendor():
    if request.method == 'POST':
        vendor_name = request.form['vendor_name']
        gst = request.form['gst']
        pan = request.form['pan']
        bank_name = request.form['bank_name']
        branch = request.form['branch']
        account_no = request.form['account_no']
        ifsc = request.form['ifsc']
        communication_data = request.form.getlist('comm_data[]')  # List of comm rows

        cur.execute("""
            INSERT INTO vendors (vendor_name, gst, pan, bank_name, branch, account_no, ifsc)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (vendor_name, gst, pan, bank_name, branch, account_no, ifsc))
        vendor_id = cur.fetchone()[0]

        for data in communication_data:
            name, mobile, email, designation = data.split('|')
            cur.execute("""
                INSERT INTO vendor_contacts (vendor_id, contact_name, mobile, email, designation)
                VALUES (%s, %s, %s, %s, %s)
            """, (vendor_id, name, mobile, email, designation))

        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('register_vendor.html')

# =====================
# Employee Registration
# =====================
@app.route('/register_employee', methods=['GET', 'POST'])
def register_employee():
    if request.method == 'POST':
        # Handle employee form data
        # ...
        return redirect(url_for('dashboard'))
    return render_template('register_employee.html')


# =====================
# Enquiry - New Project
# =====================
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        enquiry_id = request.form['enquiry_id']
        quotation = request.form['quotation']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        location = request.form['location']
        source_drawing = request.files['source_drawing']
        vendor_id = request.form['vendor_id']
        notes = request.form['notes']
        email = request.form['email']
        contact_number = request.form['contact_number']
        project_incharge = request.form['project_incharge']

        filename = ''
        if source_drawing:
            filename = os.path.join('uploads', source_drawing.filename)
            source_drawing.save(filename)

        cur.execute("""
            INSERT INTO projects (enquiry_id, quotation, start_date, end_date, location, source_drawing, vendor_id,
                                  notes, email, contact_number, project_incharge)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (enquiry_id, quotation, start_date, end_date, location, filename, vendor_id,
              notes, email, contact_number, project_incharge))
        conn.commit()

        return redirect(url_for('new_project'))

    cur.execute("SELECT id, vendor_name FROM vendors")
    vendors = cur.fetchall()

    cur.execute("SELECT * FROM projects ORDER BY id DESC")
    all_projects = cur.fetchall()

    return render_template('new_project.html', vendors=vendors, all_projects=all_projects)

# ==========================
# Measurement Sheet (Page)
# ==========================
@app.route('/add_measurement_sheet')
def add_measurement_sheet():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('measurement_sheet.html')

# Store measurements temporarily
measurement_entries = []



import math
import datetime
from fpdf import FPDF
import xlsxwriter

# ================
# AREA CALCULATION
# ================
def calculate_area(entry):
    duct_type = entry['duct_type']
    w1 = float(entry.get('w1', 0))
    h1 = float(entry.get('h1', 0))
    w2 = float(entry.get('w2', 0))
    h2 = float(entry.get('h2', 0))
    length = float(entry.get('length', 0))
    degree = float(entry.get('degree', 0))
    qty = float(entry.get('qty', 0))
    factor = float(entry.get('factor', 1))

    if duct_type == "st":
        return 2*(w1+h1)/1000*(length/1000)*qty
    elif duct_type == "red":
        return (w1+h1+w2+h2)/1000*(length/1000)*qty*factor
    elif duct_type == "dm":
        return (w1*h1)/1000000*qty
    elif duct_type == "offset":
        return (w1+h1+w2+h2)/1000*((length+degree)/1000)*qty*factor
    elif duct_type == "shoe":
        return (w1+h1)*2/1000*(length/1000)*qty*factor
    elif duct_type == "vanes":
        return (w1/1000)*(2*3.1416*(w1/1000)/4)*qty
    elif duct_type == "elb":
        arc = ((h1/2)/1000 + (length/1000)*3.1416*(degree/180))
        return 2*(w1+h1)/1000*qty*factor
    else:
        return 0


def calculate_gauge(area):
    if area <= 0.75:
        return "24g"
    elif area <= 1.2:
        return "22g"
    elif area <= 1.8:
        return "20g"
    else:
        return "18g"


# ====================
# Add Measurement Entry
# ====================
@app.route('/add_measurement', methods=['POST'])
def add_measurement():
    data = request.get_json()
    area = calculate_area(data)
    gauge = calculate_gauge(area)
    data['area'] = round(area, 3)
    data['gauge'] = gauge
    measurement_entries.append(data)
    return jsonify({'status': 'success', 'data': data})


# ====================
# Get All Measurements
# ====================
@app.route('/get_measurements')
def get_measurements():
    return jsonify(measurement_entries)


# ===================
# Delete Measurement
# ===================
@app.route('/delete_measurement/<int:index>', methods=['POST'])
def delete_measurement(index):
    if 0 <= index < len(measurement_entries):
        del measurement_entries[index]
        return jsonify({'status': 'deleted'})
    return jsonify({'status': 'error'})


# ====================
# Submit Measurements
# ====================
@app.route('/submit_measurements', methods=['POST'])
def submit_measurements():
    # Placeholder for DB commit if needed
    measurement_entries.clear()
    return jsonify({'status': 'submitted'})


# ====================
# Export to PDF
# ====================
@app.route('/export_pdf')
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Measurement Sheet", ln=True, align='C')
    pdf.ln(10)

    for i, entry in enumerate(measurement_entries):
        line = f"{i+1}. {entry}"
        pdf.multi_cell(0, 10, txt=line)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.ln(10)
    pdf.cell(0, 10, f"Prepared By: Design Engineer – {now}", ln=True)
    pdf.cell(0, 10, f"Checked By: Project Manager – {now}", ln=True)
    pdf.cell(0, 10, f"Approved By: MD – {now}", ln=True)

    output_path = "static/measurement_sheet.pdf"
    pdf.output(output_path)
    return send_file(output_path, as_attachment=True)


# =====================
# Export to Excel
# =====================
@app.route('/export_excel')
def export_excel():
    filename = "static/measurement_sheet.xlsx"
    workbook = xlsxwriter.Workbook(filename)
    sheet = workbook.add_worksheet()

    headers = list(measurement_entries[0].keys()) if measurement_entries else []
    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    for row, entry in enumerate(measurement_entries, start=1):
        for col, key in enumerate(headers):
            sheet.write(row, col, str(entry.get(key, '')))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.write(len(measurement_entries)+2, 0, f"Prepared By: Design Engineer – {now}")
    sheet.write(len(measurement_entries)+3, 0, f"Checked By: Project Manager – {now}")
    sheet.write(len(measurement_entries)+4, 0, f"Approved By: MD – {now}")

    workbook.close()
    return send_file(filename, as_attachment=True)



# ========================
# Login Page & Authentication
# ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        # Dummy check
        if user == 'admin' and pwd == 'admin':
            session['user'] = user
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')


# ========================
# Logout
# ========================
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ========================
# Dashboard
# ========================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# ========================
# Utility - Check Login
# ========================
@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect(url_for('login'))


# ========================
# Main
# ========================
if __name__ == "__main__":
    app.run(debug=True)


