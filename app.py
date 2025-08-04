from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Dummy login credentials
users = {
    'admin': 'password123',
    'user1': 'user123'
}

# Dummy vendor database
vendors_db = [
    {
        'id': 1,
        'vendor_name': 'ABC Ducts Ltd',
        'gst': '29ABCDE1234F2Z5',
        'address': 'Chennai, Tamil Nadu'
    },
    {
        'id': 2,
        'vendor_name': 'SteelFab Solutions',
        'gst': '27STFAB6789G1Z6',
        'address': 'Bangalore, Karnataka'
    }
]

# Dummy projects
projects_db = []

# ---------- ROUTES ----------

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/register')
def register():
    return redirect(url_for('vendor_registration'))

@app.route('/vendor-registration', methods=['GET', 'POST'])
def vendor_registration():
    if request.method == 'POST':
        vendor = {
            'id': len(vendors_db) + 1,
            'vendor_name': request.form['vendor_name'],
            'gst': request.form['gst'],
            'pan': request.form['pan'],
            'bank_name': request.form['bank_name'],
            'branch': request.form['branch'],
            'account_no': request.form['account_no'],
            'ifsc': request.form['ifsc'],
            'address': request.form['address'],
            'communications': []
        }
        names = request.form.getlist('contact_name[]')
        mobiles = request.form.getlist('mobile[]')
        emails = request.form.getlist('email[]')
        designations = request.form.getlist('designation[]')
        for i in range(len(names)):
            vendor['communications'].append({
                'name': names[i],
                'mobile': mobiles[i],
                'email': emails[i],
                'designation': designations[i]
            })
        vendors_db.append(vendor)
        return redirect(url_for('dashboard'))
    return render_template('vendor_registration.html')

@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        enquiry_id = request.form['enquiry_id']
        quotation = request.form['quotation']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        location = request.form['location']
        vendor_id = int(request.form['vendor_name'])
        email = request.form['email']
        contact = request.form['contact']
        incharge = request.form['incharge']
        notes = request.form['notes']
        
        drawing = request.files['drawing']
        drawing_filename = ''
        if drawing and drawing.filename != '':
            drawing_filename = drawing.filename
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            drawing.save(os.path.join(app.config['UPLOAD_FOLDER'], drawing_filename))
        
        project = {
            'enquiry_id': enquiry_id,
            'quotation': quotation,
            'start_date': start_date,
            'end_date': end_date,
            'location': location,
            'vendor_id': vendor_id,
            'vendor_name': next((v['vendor_name'] for v in vendors_db if v['id'] == vendor_id), ''),
            'gst': next((v['gst'] for v in vendors_db if v['id'] == vendor_id), ''),
            'address': next((v['address'] for v in vendors_db if v['id'] == vendor_id), ''),
            'email': email,
            'contact': contact,
            'incharge': incharge,
            'notes': notes,
            'drawing': drawing_filename
        }
        projects_db.append(project)
        return redirect(url_for('new_project'))

    enquiry_id = f"VE/TN/2526/E{str(len(projects_db)+1).zfill(3)}"
    return render_template('new_project.html', enquiry_id=enquiry_id, vendors=vendors_db, projects=projects_db)

@app.route('/get_vendor_info/<int:vendor_id>')
def get_vendor_info(vendor_id):
    vendor = next((v for v in vendors_db if v['id'] == vendor_id), None)
    if vendor:
        return jsonify({'gst': vendor['gst'], 'address': vendor['address']})
    return jsonify({'gst': '', 'address': ''})

# --------- OTHER PLACEHOLDER ROUTES ----------

@app.route('/enquiry_progress')
def enquiry_progress():
    return "Enquiry Progress Table Page"

@app.route('/enquiry_summary')
def enquiry_summary():
    return "Enquiry Summary Page"

@app.route('/production_project')
def production_project():
    return "Production New Project Page"

@app.route('/production_progress')
def production_progress():
    return "Production Progress Table Page"

@app.route('/production_summary')
def production_summary():
    return "Production Summary Page"

@app.route('/sheet_cutting')
def sheet_cutting():
    return "Sheet Cutting Page"

@app.route('/fabrication')
def fabrication():
    return "Fabrication Page"

@app.route('/dispatch')
def dispatch():
    return "Dispatch Page"

@app.route('/daily_reports')
def daily_reports():
    return "Daily Reports Page"

@app.route('/weekly_reports')
def weekly_reports():
    return "Weekly Reports Page"

@app.route('/monthly_reports')
def monthly_reports():
    return "Monthly Reports Page"

@app.route('/employee_registration')
def employee_registration():
    return "Employee Registration Page"

@app.route('/vendor_registration')
def vendor_registration():
    return "Vendor Registration Page"

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
