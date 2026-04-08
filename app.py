from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import datetime

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# Database Configuration
# ─────────────────────────────────────────────
DB_CONFIG = {
    'host': 'localhost',
    'port': 3006,
    'user': 'root',
    'password': 'Manikanta@2006',
    'database': 'HospitalDB'
}

def get_db_connection():
    """Create and return a new database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


# ─────────────────────────────────────────────
# VIEW ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/staff-dashboard')
def staff_dashboard():
    return render_template('staff_dashboard.html')


# ─────────────────────────────────────────────
# PHASE 1 — Test Route
# ─────────────────────────────────────────────

@app.route('/api/departments', methods=['GET'])
def get_departments():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM DEPARTMENT")
        departments = cursor.fetchall()
        return jsonify(departments), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# PHASE 2 — Authentication
# ─────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM USER_ACCOUNT WHERE Username = %s AND Password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            return jsonify({
                'message': 'Login successful',
                'Role':     user.get('Role'),
                'DoctorID': user.get('DoctorID'),
                'StaffID':  user.get('StaffID'),
                'Username': user.get('Username')
            }), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# PHASE 3 — Doctor Dashboard API
# ─────────────────────────────────────────────

@app.route('/api/doctor/<int:doctor_id>/appointments', methods=['GET'])
def get_doctor_appointments(doctor_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                A.AppointmentID,
                A.ApptDate,
                A.ApptTime,
                A.Status,
                P.FirstName AS PatientFirstName,
                P.LastName  AS PatientLastName
            FROM APPOINTMENT A
            JOIN PATIENT P ON A.PatientID = P.PatientID
            WHERE A.DoctorID = %s
            ORDER BY A.ApptDate ASC, A.ApptTime ASC
        """
        cursor.execute(query, (doctor_id,))
        appointments = cursor.fetchall()

        # Convert date/time objects to strings for JSON serialization
        for appt in appointments:
            if appt.get('ApptDate'):
                appt['ApptDate'] = str(appt['ApptDate'])
            if appt.get('ApptTime'):
                appt['ApptTime'] = str(appt['ApptTime'])

        return jsonify(appointments), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# PHASE 4 — Staff / Receptionist Dashboard API
# ─────────────────────────────────────────────

@app.route('/api/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT PatientID, FirstName, LastName, Phone FROM PATIENT")
        patients = cursor.fetchall()
        return jsonify(patients), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DoctorID, FirstName, LastName, Specialization FROM DOCTOR")
        doctors = cursor.fetchall()
        return jsonify(doctors), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    required = ['PatientID', 'DoctorID', 'ApptDate', 'ApptTime']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields: PatientID, DoctorID, ApptDate, ApptTime'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO APPOINTMENT (PatientID, DoctorID, ApptDate, ApptTime, Status)
            VALUES (%s, %s, %s, %s, 'Scheduled')
        """
        cursor.execute(query, (
            data['PatientID'],
            data['DoctorID'],
            data['ApptDate'],
            data['ApptTime']
        ))
        conn.commit()
        return jsonify({
            'message': 'Appointment booked successfully',
            'AppointmentID': cursor.lastrowid
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# PHASE 5 — Clinical Workflow (Medical Records)
# ─────────────────────────────────────────────

@app.route('/api/medical-records', methods=['POST'])
def create_medical_record():
    data = request.get_json()
    required = ['PatientID', 'DoctorID', 'Diagnosis', 'Prescription']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields: PatientID, DoctorID, Diagnosis, Prescription'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        today = datetime.date.today()
        cursor = conn.cursor()
        query = """
            INSERT INTO MEDICAL_RECORD (DateRecorded, Diagnosis, Prescription, PatientID, DoctorID)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            today,
            data['Diagnosis'],
            data['Prescription'],
            data['PatientID'],
            data['DoctorID']
        ))
        conn.commit()
        return jsonify({
            'message': 'Medical record saved successfully',
            'RecordID': cursor.lastrowid,
            'DateRecorded': str(today)
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
