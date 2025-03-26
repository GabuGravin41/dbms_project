from flask import Flask, render_template, request, redirect, url_for, flash
import MySQLdb
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database Configuration
db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="dalton",
    db="new_mydb",
    charset="utf8"
)
cursor = db.cursor()

#def insert_default_data():
#    # Insert Default Doctors if not exists
#    cursor.execute("SELECT COUNT(*) FROM doctor")
#    if cursor.fetchone()[0] == 0:
#        cursor.executemany(
#            "INSERT INTO doctor (contract_no, speciality) VALUES (%s, %s)",
#            [('DOC001', 'Surgeon'), ('DOC002', 'Orthopedic'), ('DOC003', 'Anesthesiologist')]
#        )
    
#    # Insert Default Patients if not exists
#    cursor.execute("SELECT COUNT(*) FROM patient")
#    if cursor.fetchone()[0] == 0:
#        cursor.executemany(
#            "INSERT INTO patient (display_file_no, phone_no, GPS_location, physical_address, contact_phone_no) VALUES (%s, %s, %s, %s, %s)",
#            [
#                ('Lutomia Onchari (PF-5001)','1234567890', '37.7749,-122.4194', '123 Main St, NY', '9876543210'),
#                ('Wanjeri Waweru (PF-4896)','2345678901', '40.7128,-74.0060', '456 Elm St, CA', '8765432109'),
#                ('Mikasa Malawi (PF-5003)','3456789012', '51.5074,-0.1278', '789 Oak St, TX', '7654321098'),
#                ('Otieno Okong\'o (PF-5014)','4567890123', '34.0522,-118.2437', '321 Pine St, FL', '6543210987'),
#                ('Lung\'azo Losusui (PF-5009)','5678901234', '48.8566,2.3522', '654 Cedar St, IL', '5432109876')
#            ]
#        )
    
#    # Insert Default Theatres if not exists
#    cursor.execute("SELECT COUNT(*) FROM theatre_status")
#    if cursor.fetchone()[0] == 0:
#        cursor.executemany(
#            "INSERT INTO theatre_status (name, status) VALUES (%s, %s)",
#            [('Theater 1', 'Available'), ('Theater 2', 'In Use'), ('Theater 3', 'Maintenance')]
#        )
    
#    db.commit()

## Run the function when the app starts
#insert_default_data()


# 🏠 Dashboard Route
@app.route("/", methods=["GET", "POST"])
def dashboard():
    # Handle Theater Status Update
    if request.method == "POST" and "update_status" in request.form:
        theater_id = request.form.get("theater_id")
        new_status = request.form.get("new_status")
        cursor.execute("UPDATE theatre_status SET status = %s WHERE theatre_id = %s", (new_status, theater_id))
        db.commit()
        flash("Theater status updated!", "success")
        return redirect(url_for("dashboard"))

    # Handle Booking Creation
    elif request.method == "POST" and "create_booking" in request.form:
        doctor_id = request.form.get("doctor_id")
        patient_id = request.form.get("patient_id")
        theater_id = request.form.get("theater_id")
        booking_time = request.form.get("booking_time")

        if doctor_id and patient_id and theater_id and booking_time:
            cursor.execute("""
                INSERT INTO booking (theatre_id, patient_file_no, doctor_contract_no, start_time, end_time, status) 
                VALUES (%s, %s, %s, %s, %s, 'Booked')
            """, (theater_id, patient_id, doctor_id, booking_time, booking_time))
            db.commit()
            flash("Theater booked successfully!", "success")
        else:
            flash("All fields are required!", "error")
        return redirect(url_for("dashboard"))

    # Handle Booking Updates (Complete/Cancel)
    elif request.method == "POST" and "update_booking" in request.form:
        booking_id = request.form.get("booking_id")
        action = request.form.get("update_booking")

        if action == "complete":
            cursor.execute("UPDATE booking SET status = 'Completed' WHERE booking_id = %s", (booking_id,))
            flash("Booking marked as completed!", "success")

        elif action == "cancel":
            cursor.execute("UPDATE booking SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,))
            flash("Booking has been cancelled!", "error")

        db.commit()
        return redirect(url_for("dashboard"))

    # Fetch Theater Statuses
    cursor.execute("SELECT theatre_id, name AS theater_no, status FROM theatre_status")
    theaters = [{"id": row[0], "theater_no": row[1], "status": row[2]} for row in cursor.fetchall()]

    # Fetch Doctors
    cursor.execute("SELECT contract_no, speciality FROM doctor")
    doctors = [{"id": row[0], "contract_no": row[0], "specialty": row[1]} for row in cursor.fetchall()]

    # Fetch Patients with their display identifier
    cursor.execute("SELECT file_no, display_file_no FROM patient")
    patients = [{"id": row[0], "display_file_no": row[1]} for row in cursor.fetchall()]

    # Fetch Bookings
    cursor.execute("""
        SELECT b.booking_id, t.name AS theater_no, b.start_time, d.contract_no, p.file_no, b.status 
        FROM booking b
        JOIN theatre_status t ON b.theatre_id = t.theatre_id
        JOIN doctor d ON b.doctor_contract_no = d.contract_no
        JOIN patient p ON b.patient_file_no = p.file_no
        ORDER BY b.start_time DESC
    """)
    bookings = [{"id": row[0], "theater": {"theater_no": row[1]}, "booking_time": row[2],
                 "doctor": {"contract_no": row[3]}, "patient": {"file_no": row[4]}, "status": row[5]}
                for row in cursor.fetchall()]

    # Fetch Monthly Statistics
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT COUNT(*) AS bookings_count, SUM(TIMESTAMPDIFF(HOUR, start_time, end_time)) AS actual_usage 
        FROM booking WHERE DATE_FORMAT(start_time, '%%Y-%%m') = %s
    """, (current_month,))
    stats = cursor.fetchone()
    monthly_stats = {"bookings_count": stats[0] or 0, "actual_usage": stats[1] or 0}

    return render_template("dashboard.html", theaters=theaters, doctors=doctors,
                           patients=patients, bookings=bookings, monthly_stats=monthly_stats)


@app.route("/theatre-schedule")
def theatre_schedule():
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] 
    cursor.execute("SELECT doctor.contract_no, start_time FROM booking INNER JOIN doctor ON booking.doctor_contract_no = doctor.contract_no ORDER BY start_time") 
    schedule = [{"doctor": row[0], "start_time": row[1]} for row in cursor.fetchall()] 
    return render_template("theatre_schedule.html", days_of_week=days_of_week, schedule=schedule)


# 🩺 Doctors List Route
@app.route("/doctors")
def list_doctors():
    cursor.execute("SELECT contract_no, speciality FROM doctor")
    doctors = [{"id": row[0], "contract_no": row[0], "specialty": row[1]} for row in cursor.fetchall()]
    return render_template("doctors.html", doctors=doctors)

# 🧑‍⚕️ Doctor Profile Route
@app.route("/doctor-profile")
def doctor_profile():
    doctor_id = request.args.get('id')
    cursor.execute("SELECT contract_no, speciality FROM doctor WHERE contract_no = %s", (doctor_id,))
    doctor = cursor.fetchone()
    if doctor:
        return render_template("doctor-profile.html", doctor={"contract_no": doctor[0], "specialization": doctor[1]})
    else:
        flash("Doctor not found!", "error")
        return redirect(url_for("list_doctors"))

# 🧑‍⚕️ Patients List Route
@app.route("/patients")
def list_patients():
    cursor.execute("SELECT file_no, display_file_no FROM patient")
    patients = [{"id": row[0], "display_file_no": row[1]} for row in cursor.fetchall()]
    return render_template("patients.html", patients=patients)

# 🧑‍⚕️ Patient Profile Route
@app.route("/patient-profile")
def patient_profile():
    patient_id = request.args.get('id')
    cursor.execute("SELECT file_no, display_file_no FROM patient WHERE file_no = %s", (patient_id,))
    patient = cursor.fetchone()
    if patient:
        return render_template("patient-profile.html", patient={"file_no": patient[0], "display_file_no": patient[1]})
    else:
        flash("Patient not found!", "error")
        return redirect(url_for("list_patients"))

if __name__ == "__main__":
    app.run(debug=True)
