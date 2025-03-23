import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from db import get_db_connection

driver_dashboard = Blueprint("driver_dashboard", __name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Uploading Image if not present in the Profile Page
@driver_dashboard.route("/upload_image", methods=["POST"])
def upload_image():
    if 'image' not in request.files or 'email' not in session:
        flash("No file selected or session expired", "danger")
        return redirect(request.referrer)

    file = request.files['image']
    image_type = request.form.get('image_type')  
    email = session['email']  

    if file and allowed_file(file.filename):
        #Getting accurate file path
        filename = secure_filename(f"{image_type}_{email}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join("uploads", filename).replace("\\", "/")  
        file.save(os.path.join(UPLOAD_FOLDER, filename))  

        conn = get_db_connection()
        cur = conn.cursor()

        #Updating in database
        if image_type == "driver":
            cur.execute("UPDATE drivers SET driver_image = %s WHERE email = %s", (file_path, email))
        elif image_type == "license":
            cur.execute("UPDATE drivers SET license_image = %s WHERE email = %s", (file_path, email))

        conn.commit()
        cur.close()
        conn.close()

        flash("Image uploaded successfully!", "success")
        return redirect(request.referrer)  

    flash("Invalid file type. Please upload a PNG, JPG, JPEG, or GIF.", "danger")
    return redirect(request.referrer)

# Profile page for the driver
@driver_dashboard.route("/profile")
def profile():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))

    email = session['email']

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch Details
    cur.execute("""
        SELECT full_name, email, phone, license_number, vehicle_type, driver_image, license_image
        FROM drivers WHERE email = %s
    """, (email,))

    driver = cur.fetchone()
    cur.close()
    conn.close()

    if not driver:
        flash("Driver details not found. Please complete onboarding.", "danger")
        return redirect(url_for("driver_dashboard.dashboard"))

    full_name, email, phone, license_number, vehicle_type, driver_image, license_image = driver

    return render_template("driverprofile.html",
                           full_name=full_name,
                           email=email,
                           phone=phone,
                           license_number=license_number,
                           vehicle_type=vehicle_type,
                           driver_image=driver_image,
                           license_image=license_image)

# Driver onboarding form
@driver_dashboard.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    #When not logged in/ Accidentally reaching this page without logging in
    if 'email' not in session:
        return redirect(url_for("blueprints.home"))  

    email = session['email']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        full_name = request.form.get("full_name")
        license_number = request.form.get("license_number")
        vehicle_type = request.form.get("vehicle_type")

        if 'license_image' in request.files:
            file = request.files['license_image']
            if file and allowed_file(file.filename):
                #get the accurate path for file
                filename = secure_filename(f"license_{email}.{file.filename.rsplit('.', 1)[1].lower()}")  
                file_path = os.path.join("uploads", filename).replace("\\", "/")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                cur.execute("UPDATE drivers SET license_image = %s WHERE email = %s", (file_path, email)) # add the path in database

        #Update the details
        cur.execute("""
            UPDATE drivers 
            SET full_name = %s, license_number = %s, vehicle_type = %s, completed_onboarding = TRUE
            WHERE email = %s
        """, (full_name, license_number, vehicle_type, email))

        conn.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("driver_dashboard.profile")) 

    # Fetch to display later
    cur.execute("""
        SELECT full_name, email, phone, license_number, vehicle_type, driver_image, license_image, completed_onboarding 
        FROM drivers WHERE email = %s
    """, (email,))
    
    driver = cur.fetchone()
    cur.close()
    conn.close()

    if not driver:
        flash("Driver details not found. Please complete onboarding.", "warning")
        return redirect(url_for("blueprints.logout"))

    full_name, email, phone, license_number, vehicle_type, driver_image, license_image, completed_onboarding = driver

    return render_template("driver_dashboard.html", 
                           full_name=full_name, 
                           email=email, 
                           phone=phone,
                           license_number=license_number,
                           vehicle_type=vehicle_type,
                           driver_image=driver_image,
                           license_image=license_image,
                           completed_onboarding=completed_onboarding)


@driver_dashboard.route('/DriverRequest')
def DriverRequest():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))  # Redirect if not logged in

    email = session['email']
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch the driver's request status
    cur.execute("SELECT vehicle_type, request_status FROM drivers WHERE email = %s", (email,))
    result = cur.fetchone()

    if not result or not result[0]:  
        flash("Vehicle type not found. Please update your profile.", "warning")
        return redirect(url_for("driver_dashboard.dashboard"))

    vehicle_type, request_status = result  

    # Fetch vehicles of the same type from the vehicles table
    cur.execute("""
        SELECT vehiclename, brand, image_link, availability 
        FROM vehicles 
        WHERE type = %s
    """, (vehicle_type,))
    vehicles = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('DriverRequest.html', 
                           vehicles=vehicles, 
                           vehicle_type=vehicle_type, 
                           request_status=request_status)


import json
from flask import jsonify

# Submit the selected vehicles request
@driver_dashboard.route("/submit_vehicle_request", methods=["POST"])
def submit_vehicle_request():
    if 'email' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 403

    # Get the generated list by the user
    data = request.get_json()
    vehicles_requested = data.get("vehicles", [])
    email = session["email"]

    if not vehicles_requested:
        return jsonify({"status": "error", "message": "No vehicles selected"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Insert into vehicle_requests table
    cur.execute("""
        INSERT INTO vehicle_requests (driver_email, requested_vehicles, status)
        VALUES (%s, %s, 'pending')
    """, (email, ", ".join(vehicles_requested)))

    # Update request_status
    cur.execute("""
        UPDATE drivers SET request_status = 'sent' WHERE email = %s
    """, (email,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success", "message": "Request submitted successfully"})

# See the current assigned vehicle to the user
@driver_dashboard.route("/assigned_vehicle")
def assigned_vehicle():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))

    email = session['email']
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT v.image_link, d.vehicle_name, d.vehicle_brand, d.vehicle_plate_number
        FROM vehicles v
        JOIN drivers d ON d.email = %s AND d.vehicle_assigned = TRUE
        WHERE v.vehiclename = d.vehicle_name 
    """, (email,))

    vehicle = cur.fetchone()

    cur.close()
    conn.close()

    if not vehicle:
        flash("No vehicle assigned to you.", "danger")
        return redirect(url_for("driver_dashboard.profile"))

    # For easier visualization
    assigned_vehicle = {
        'image_link': vehicle[0],  
        'name': vehicle[1],        
        'brand': vehicle[2],       
        'plate_number': vehicle[3] 
    }

    return render_template("assigned_vehicle.html", assigned_vehicle=assigned_vehicle)

# Remove vehicle assigned
@driver_dashboard.route("/release_vehicle", methods=["POST"])
def release_vehicle():
    if 'email' not in session:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for("blueprints.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch
        cur.execute("""
            SELECT vehicle_name, vehicle_plate_number 
            FROM drivers 
            WHERE email = %s AND vehicle_assigned = TRUE
        """, (session['email'],))
        
        vehicle = cur.fetchone()

        if not vehicle:
            flash("No vehicle currently assigned to you.", "warning")
            return redirect(url_for("driver_dashboard.assigned_vehicle"))

        vehicle_name, plate_number = vehicle

        # Mark vehicle as available again
        cur.execute("""
            UPDATE assigned_vehicles 
            SET assigned_status = FALSE 
            WHERE vehicle_plate = %s
        """, (plate_number,))

        # Increase availability
        cur.execute("""
            UPDATE vehicles 
            SET availability = availability + 1 
            WHERE vehiclename = %s
        """, (vehicle_name,))

        # Reset driver vehicle information
        cur.execute("""
            UPDATE drivers 
            SET vehicle_assigned = FALSE, 
                vehicle_name = NULL, 
                vehicle_plate_number = NULL, 
                vehicle_brand = NULL, 
                request_status = 'none'
            WHERE email = %s
        """, (session['email'],))

        conn.commit()
        flash("You have successfully released the assigned vehicle.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("driver_dashboard.profile"))
