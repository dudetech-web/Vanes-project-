from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy login credentials
users = {
    'admin': 'password123',
    'user1': 'user123'
}

# Dummy vendor database
vendors_db = [
    {
        'vendor_name': 'ABC Ducts Ltd',
        'gst': '29ABCDE1234F2Z5',
        'pan': 'ABCDE1234F',
        'bank_name': 'State Bank of India',
        'branch': 'MG Road',
        'account_no': '12345678901',
        'ifsc': 'SBIN0001234',
        'communications': [
            {'name': 'Raj Kumar', 'mobile': '9876543210', 'email': 'raj@abc.com', 'designation': 'Manager'},
            {'name': 'Anjali Mehta', 'mobile': '9123456789', 'email': 'anjali@abc.com', 'designation': 'Engineer'}
        ]
    },
    {
        'vendor_name': 'SteelFab Solutions',
        'gst': '27STFAB6789G1Z6',
        'pan': 'STFAB6789G',
        'bank_name': 'HDFC Bank',
        'branch': 'Indiranagar',
        'account_no': '98765432109',
        'ifsc': 'HDFC0009876',
        'communications': [
            {'name': 'Kiran Rao', 'mobile': '9090909090', 'email': 'kiran@steelfab.com', 'designation': 'Director'}
        ]
    }
]

# Dummy project DB
projects_db = []

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
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/vendor-registration', methods=['GET', 'POST'])
def vendor_registration():
    if request.method == 'POST':
        vendor = {
            'vendor_name': request.form['vendor_name'],
            'gst': request.form['gst'],
            'pan': request.form['pan'],
            'bank_name': request.form['bank_name'],
            'branch': request.form['branch'],
            'account_no': request.form['account_no'],
            'ifsc': request.form['ifsc'],
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

# ---------------- New Project ----------------

@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        project = {
            'enquiry_id': request.form['enquiry_id'],
            'quotation': request.form['quotation'],
            'start_date': request.form['start_date'],
            'end_date': request.form['end_date'],
            'project_location': request.form['project_location'],
            'drawing_file': request.form['drawing_file'],
            'vendor_name': request.form['vendor_name'],
            'gst': request.form['gst'],
            'address': request.form['address'],
            'notes': request.form['notes'],
            'email': request.form['email'],
            'contact_number': request.form['contact_number'],
            'project_incharge': request.form['project_incharge']
        }
        projects_db.append(project)
        return redirect(url_for('new_project'))
    
    return render_template('new_project.html', vendors=vendors_db, projects=projects_db)

@app.route('/get_vendor_info', methods=['POST'])
def get_vendor_info():
    vendor_name = request.form['vendor_name']
    for vendor in vendors_db:
        if vendor['vendor_name'] == vendor_name:
            return jsonify({
                'gst': vendor['gst'],
                'address': vendor['branch']  # Assuming branch as address
            })
    return jsonify({'gst': '', 'address': ''})

@app.route('/edit_project', methods=['POST'])
def edit_project():
    enquiry_id = request.form['enquiry_id']
    for project in projects_db:
        if project['enquiry_id'] == enquiry_id:
            project['quotation'] = request.form['quotation']
            project['start_date'] = request.form['start_date']
            project['end_date'] = request.form['end_date']
            project['project_location'] = request.form['project_location']
            project['project_incharge'] = request.form['project_incharge']
            project['contact_number'] = request.form['contact_number']
            project['email'] = request.form['email']
            project['notes'] = request.form['notes']
            break
    return jsonify({'status': 'success'})

@app.route('/delete_project', methods=['POST'])
def delete_project():
    enquiry_id = request.form['enquiry_id']
    global projects_db
    projects_db = [p for p in projects_db if p['enquiry_id'] != enquiry_id]
    return jsonify({'status': 'deleted'})

@app.route('/add_measurement_sheet/<enquiry_id>')
def add_measurement_sheet(enquiry_id):
    return f"Measurement Sheet Page for {enquiry_id}"

# ---------------- Placeholder Routes ----------------

@app.route('/enquiry_progress')
def enquiry_progress():
    # Dummy project progress data (you can later fetch from DB)
    progress_data = [
        {
            'enquiry_id': 'VE/TN/2526/E001',
            'vendor': 'ABC Ducts Ltd',
            'location': 'Chennai',
            'start_date': '2025-08-01',
            'end_date': '2025-09-15',
            'incharge': 'Ravi Kumar',
            'stage': 'Drawing',
            'status': 'In Progress',
            'remarks': '-'
        },
        {
            'enquiry_id': 'VE/TN/2526/E002',
            'vendor': 'SteelFab Solutions',
            'location': 'Bangalore',
            'start_date': '2025-08-03',
            'end_date': '2025-09-20',
            'incharge': 'Anita Joshi',
            'stage': 'Production',
            'status': 'Completed',
            'remarks': 'Ready for dispatch'
        }
    ]
    return render_template('enquiry_progress.html', progress_data=progress_data)"

@app.route('/enquiry_summary')
def enquiry_summary():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('enquiry_summary.html')

@app.route('/production_project')
def production_project_view():
    # Filter only approved enquiry projects
    approved_projects = [p for p in enquiry_projects if p.get('approved') == True]

    return render_template('production_project.html', approved_projects=approved_projects)

@app.route('/production_progress', methods=['GET', 'POST'])
def production_progress_view():
    if request.method == 'POST':
        enquiry_id = request.form['enquiry_id']
        new_status = request.form['status']
        # Update status in the dummy list
        for project in production_progress:
            if project['enquiry_id'] == enquiry_id:
                project['status'] = new_status
                break
        return redirect(url_for('production_progress_view'))

    return render_template('production_progress.html', progress_data=production_progress)

@app.route('/production_summary')
def production_summary():
    # Dummy data for demonstration
    summary_data = [
        {
            'project_name': 'Project Alpha',
            'status': 'Ongoing',
            'start_date': '2025-07-01',
            'end_date': '2025-08-10',
            'total_ducts': 56,
            'total_area': 845.5
        },
        {
            'project_name': 'Project Beta',
            'status': 'Completed',
            'start_date': '2025-06-01',
            'end_date': '2025-07-15',
            'total_ducts': 73,
            'total_area': 1024.3
        }
    ]
    return render_template("production_summary.html", summary=summary_data)

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

@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "dob": request.form['dob'],
            "gender": request.form['gender'],
            "marital_status": request.form['marital_status'],
            "aadhaar": request.form['aadhaar'],
            "pan": request.form['pan'],
            "esi": request.form['esi'],
            "designation": request.form['designation'],
            "location": request.form['location'],
            "doj": request.form['doj'],
            "employment_type": request.form['employment_type'],
            "bank_name": request.form['bank_name'],
            "branch": request.form['branch'],
            "account_no": request.form['account_no'],
            "ifsc": request.form['ifsc'],
            "emergency_name": request.form['emergency_name'],
            "emergency_relation": request.form['emergency_relation'],
            "emergency_mobile": request.form['emergency_mobile'],
            "blood_group": request.form['blood_group'],
            "allergies": request.form['allergies'],
            "medical_conditions": request.form['medical_conditions'],
            "reference_name": request.form['reference_name'],
            "reference_mobile": request.form['reference_mobile'],
            "reference_relation": request.form['reference_relation']
        }
        # Optional: Save `data` to your database here.
        print("Received Employee Data:", data)
        return redirect(url_for('dashboard'))  # or wherever you want to redirect after save

    return render_template('employee_registration.html')

if __name__ == '__main__':
    app.run(debug=True)
