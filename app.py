from flask import Flask, render_template, request, redirect, url_for, session

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

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f"Welcome {session['user']}! This is the dashboard."

@app.route('/register')
def register():
    return redirect(url_for('vendor_registration'))

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
