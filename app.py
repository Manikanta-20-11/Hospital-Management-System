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

@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


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
                A.PatientID,
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


@app.route('/api/patients', methods=['POST'])
def register_patient():
    data = request.get_json()
    required = ['FirstName', 'LastName', 'DOB', 'Gender', 'Phone', 'Address']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO PATIENT (FirstName, LastName, DOB, Gender, Phone, Address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['FirstName'],
            data['LastName'],
            data['DOB'],
            data['Gender'],
            data['Phone'],
            data['Address']
        ))
        conn.commit()
        return jsonify({
            'message': 'Patient registered successfully',
            'PatientID': cursor.lastrowid
        }), 201
    except Error as e:
        conn.rollback()
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
# PHASE 6 — Admissions & Ward
# ─────────────────────────────────────────────

@app.route('/api/active-admissions', methods=['GET'])
def get_active_admissions():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                A.AdmissionID,
                P.PatientID,
                P.FirstName,
                P.LastName,
                A.RoomNumber,
                A.AdmissionDate
            FROM ADMISSION A
            JOIN PATIENT P ON A.PatientID = P.PatientID
            JOIN ROOM R ON A.RoomNumber = R.RoomNumber
            WHERE A.DischargeDate IS NULL
        """
        cursor.execute(query)
        admissions = cursor.fetchall()

        for a in admissions:
            if a.get('AdmissionDate'):
                a['AdmissionDate'] = str(a['AdmissionDate'])

        return jsonify(admissions), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/discharge', methods=['POST'])
def discharge_patient():
    data = request.get_json()
    required = ['AdmissionID', 'PatientID']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields: AdmissionID, PatientID'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        today = datetime.date.today()

        # Get admission and room info to calculate charge
        cursor.execute("""
            SELECT A.AdmissionDate, R.DailyRate
            FROM ADMISSION A
            JOIN ROOM R ON A.RoomNumber = R.RoomNumber
            WHERE A.AdmissionID = %s
        """, (data['AdmissionID'],))
        adm_info = cursor.fetchone()

        if not adm_info:
            return jsonify({'error': 'Admission record not found'}), 404

        days = (today - adm_info['AdmissionDate']).days
        charge_days = max(1, days)
        total_amount = float(charge_days * adm_info['DailyRate'])

        # Step A: Update DischargeDate
        cursor.execute("""
            UPDATE ADMISSION
            SET DischargeDate = %s
            WHERE AdmissionID = %s
        """, (today, data['AdmissionID']))

        # Step B/C: Insert Bill
        cursor.execute("""
            INSERT INTO BILLING (TotalAmount, PaymentStatus, BillingDate, PatientID)
            VALUES (%s, 'Pending', %s, %s)
        """, (total_amount, today, data['PatientID']))

        conn.commit()
        return jsonify({'message': 'Patient Discharged & Bill Generated!'}), 200
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()



# ─────────────────────────────────────────────
# PHASE 6b — Admissions Workflow
# ─────────────────────────────────────────────

@app.route('/api/available-rooms', methods=['GET'])
def get_available_rooms():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT RoomNumber, RoomType
            FROM ROOM
            WHERE RoomNumber NOT IN (
                SELECT RoomNumber FROM ADMISSION WHERE DischargeDate IS NULL
            )
            ORDER BY RoomNumber
        """
        cursor.execute(query)
        rooms = cursor.fetchall()
        return jsonify(rooms), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admissions', methods=['POST'])
def admit_patient():
    data = request.get_json()
    required = ['PatientID', 'DoctorID', 'RoomNumber']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields: PatientID, DoctorID, RoomNumber'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO ADMISSION (AdmissionDate, DischargeDate, PatientID, RoomNumber, DoctorID)
            VALUES (CURRENT_DATE(), NULL, %s, %s, %s)
        """
        cursor.execute(query, (
            data['PatientID'],
            data['RoomNumber'],
            data['DoctorID']
        ))
        conn.commit()
        return jsonify({
            'message': 'Patient admitted successfully',
            'AdmissionID': cursor.lastrowid
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# PHASE 8b — Cashier / Payment Processing
# ─────────────────────────────────────────────

@app.route('/api/pending-bills', methods=['GET'])
def get_pending_bills():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        
        # THE FIX: Changed B.BillingID to B.BillID
        query = """
            SELECT B.BillID, P.FirstName, P.LastName, B.TotalAmount, B.BillingDate
            FROM BILLING B
            JOIN PATIENT P ON B.PatientID = P.PatientID
            WHERE B.PaymentStatus = 'Pending'
            ORDER BY B.BillingDate DESC
        """
        cursor.execute(query)
        bills = cursor.fetchall()
        
        # Convert Decimal and date objects to JSON-friendly types
        for bill in bills:
            bill['TotalAmount'] = float(bill['TotalAmount']) if bill['TotalAmount'] else 0
            bill['BillingDate'] = str(bill['BillingDate']) if bill['BillingDate'] else ''
            
        return jsonify(bills), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/pay-bill', methods=['POST'])
def pay_bill():
    data = request.get_json()
    if not data or 'BillID' not in data:
        return jsonify({'error': 'Missing BillID'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE BILLING SET PaymentStatus = 'Paid' WHERE BillID = %s", (data['BillID'],))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Bill not found or already paid'}), 404
        conn.commit()
        return jsonify({'message': 'Payment recorded successfully'}), 200
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# PHASE 7 — Admin Dashboard
# ─────────────────────────────────────────────

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) AS total FROM PATIENT")
        patients_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM DOCTOR")
        doctors_count = cursor.fetchone()['total']

        cursor.execute("SELECT SUM(TotalAmount) AS total_revenue FROM BILLING WHERE PaymentStatus = 'Paid'")
        rev_row = cursor.fetchone()
        revenue_sum = rev_row['total_revenue'] if rev_row['total_revenue'] else 0

        return jsonify({
            'total_patients': patients_count,
            'total_doctors': doctors_count,
            'total_revenue': float(revenue_sum)
        }), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/staff-list', methods=['GET'])
def get_staff_list():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT S.FirstName, S.LastName, S.Role, D.DeptName 
            FROM STAFF S 
            LEFT JOIN DEPARTMENT D ON S.DepartmentID = D.DepartmentID
        """
        cursor.execute(query)
        staff = cursor.fetchall()
        return jsonify(staff), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/search/patients', methods=['GET'])
def search_patients():
    query_param = request.args.get('q', '')
    if not query_param:
        return jsonify([])

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        search_term = f"%{query_param}%"
        query = """
            SELECT PatientID, FirstName, LastName, Phone 
            FROM PATIENT 
            WHERE FirstName LIKE %s OR LastName LIKE %s OR Phone LIKE %s
        """
        cursor.execute(query, (search_term, search_term, search_term))
        patients = cursor.fetchall()
        return jsonify(patients), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/add-doctor', methods=['POST'])
def admin_add_doctor():
    data = request.get_json()
    required = ['FirstName', 'LastName', 'Specialization', 'ContactNumber', 'DepartmentID']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO DOCTOR (FirstName, LastName, Specialization, ContactNumber, DepartmentID)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['FirstName'],
            data['LastName'],
            data['Specialization'],
            data['ContactNumber'],
            data['DepartmentID']
        ))
        conn.commit()
        return jsonify({
            'message': 'Doctor added successfully',
            'DoctorID': cursor.lastrowid
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/add-staff', methods=['POST'])
def admin_add_staff():
    data = request.get_json()
    required = ['FirstName', 'LastName', 'Role', 'ContactNumber', 'DepartmentID']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO STAFF (FirstName, LastName, Role, ContactNumber, DepartmentID)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['FirstName'],
            data['LastName'],
            data['Role'],
            data['ContactNumber'],
            data['DepartmentID']
        ))
        conn.commit()
        return jsonify({
            'message': 'Staff added successfully',
            'StaffID': cursor.lastrowid
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
