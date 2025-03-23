import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from db import get_db_connection

vendor_dashboard = Blueprint("vendor_dashboard", __name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Registration form for Vendors
@vendor_dashboard.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))  

    email = session['email']
    conn = get_db_connection()
    cur = conn.cursor()

    # Initial Fetch to fill the already known values in form
    cur.execute("""
        SELECT full_name, email, phone, business_license, vendor_image, business_license_image, vendor_level, registration_complete
        FROM vendors WHERE email = %s
    """, (email,))

    vendor = cur.fetchone()

    if vendor:
        full_name, email, phone, business_license, vendor_image, business_license_image, vendor_level, registration_complete = vendor
    else:
        flash("Vendor details not found.", "danger")
        return redirect(url_for("vendor_dashboard.dashboard"))

    if request.method == "POST":
        # Getting form data
        full_name = request.form.get("full_name")
        phone = request.form.get("phone")
        business_license = request.form.get("business_license")
        vendor_level = request.form.get("vendor_level")  # Get vendor level from form

        # Handle business license image upload
        if 'business_license_image' in request.files:
            file = request.files['business_license_image']
            if file and allowed_file(file.filename):
                # Getting Accurate File Path
                filename = secure_filename(f"business_license_{email}.{file.filename.rsplit('.', 1)[1].lower()}")
                file_path = os.path.join("uploads", filename).replace("\\", "/")
                file.save(os.path.join(UPLOAD_FOLDER, filename))

                cur.execute("UPDATE vendors SET business_license_image = %s WHERE email = %s", (file_path, email))

        # Update vendor details and mark registration as complete/true
        cur.execute("""
            UPDATE vendors
            SET full_name = %s, phone = %s, business_license = %s, vendor_level = %s, registration_complete = TRUE
            WHERE email = %s
        """, (full_name, phone, business_license, vendor_level, email))

        conn.commit()
        flash("Profile updated successfully!", "success")
        cur.close()
        conn.close()

        return redirect(url_for("vendor_dashboard.profile")) 

    cur.close()
    conn.close()

    # Make form read-only if registration is complete
    read_only = "readonly" if registration_complete else ""

    return render_template("vendor_dashboard.html", 
                           full_name=full_name, 
                           email=email, 
                           phone=phone, 
                           business_license=business_license,
                           vendor_image=vendor_image,
                           business_license_image=business_license_image,
                           vendor_level=vendor_level,  # Pass vendor level to the template
                           registration_complete=registration_complete,
                           read_only=read_only)

@vendor_dashboard.route("/upload_vendor_image", methods=["POST"])
def upload_vendor_image():
    if 'email' not in session:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for("blueprints.login"))

    email = session['email']
    file = request.files.get('vendor_image')

    if file and allowed_file(file.filename):
        filename = secure_filename(f"vendor_{email}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join("uploads", filename).replace("\\", "/")
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        # Update the vendor image path in the db
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE vendors SET vendor_image = %s WHERE email = %s", (file_path, email))
        conn.commit()
        cur.close()
        conn.close()

        flash("Vendor image uploaded successfully!", "success")
    else:
        flash("Invalid file type. Please upload a PNG, JPG, JPEG, or GIF.", "danger")

    return redirect(request.referrer)

@vendor_dashboard.route("/upload_business_license_image", methods=["POST"])
def upload_business_license_image():
    if 'email' not in session:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for("blueprints.login"))

    email = session['email']
    file = request.files.get('business_license_image')

    if file and allowed_file(file.filename):
        filename = secure_filename(f"business_license_{email}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join("uploads", filename).replace("\\", "/")
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        # Update the business license image path in the db
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE vendors SET business_license_image = %s WHERE email = %s", (file_path, email))
        conn.commit()
        cur.close()
        conn.close()

        flash("Business license image uploaded successfully!", "success")
    else:
        flash("Invalid file type. Please upload a PNG, JPG, JPEG, or GIF.", "danger")

    return redirect(request.referrer)

# Profile Page for vendor
@vendor_dashboard.route("/profile")
def profile():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))  

    email = session['email']
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch vendor profile details
    cur.execute("""
        SELECT full_name, email, phone, business_license, vendor_image, business_license_image, vendor_level
        FROM vendors WHERE email = %s
    """, (email,))

    vendor = cur.fetchone()
    cur.close()
    conn.close()

    if vendor:
        full_name, email, phone, business_license, vendor_image, business_license_image, vendor_level = vendor
    else:
        flash("Vendor details not found.", "danger")
        return redirect(url_for("vendor_dashboard.dashboard"))

    return render_template("vendorprofile.html", 
                           full_name=full_name, 
                           email=email, 
                           phone=phone, 
                           business_license=business_license,
                           vendor_image=vendor_image,
                           business_license_image=business_license_image,
                           vendor_level=vendor_level)  

# Shows pending vehicle requests
@vendor_dashboard.route("/vehicle_requests")
def vehicle_requests():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch only pending vehicle requests
    cur.execute("""
        SELECT vr.driver_email, STRING_AGG(vr.requested_vehicles, ', ') AS requested_vehicles, vr.status,
               d.full_name, d.vehicle_type, d.driver_image, d.email
        FROM vehicle_requests vr
        JOIN drivers d ON vr.driver_email = d.email
        WHERE vr.status = 'pending'
        GROUP BY vr.driver_email, d.full_name, d.vehicle_type, d.driver_image, d.email, vr.status
    """)

    requests = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("vendor_vehicle_requests.html", requests=requests)

# Page where the driver details along with their requests are shown
@vendor_dashboard.route('/review_request/<driver_email>')
def review_request(driver_email):
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetching driver details
    cur.execute("""
        SELECT full_name, email, phone, license_number, vehicle_type, driver_image, license_image
        FROM drivers WHERE email = %s
    """, (driver_email,))
    
    driver = cur.fetchone()
    
    if not driver:
        flash("Driver details not found.", "danger")
        return redirect(url_for("vendor_dashboard.vehicle_requests"))

    # Fetching requested vehicles
    cur.execute("""
        SELECT requested_vehicles FROM vehicle_requests 
        WHERE driver_email = %s AND status = 'pending'
    """, (driver_email,))
    
    requested_vehicles = cur.fetchone()
    
    if not requested_vehicles:
        flash("No requested vehicles found for this driver.", "warning")
        return redirect(url_for("vendor_dashboard.vehicle_requests"))
    
    # Requested vehicle names into a list
    requested_vehicle_list = [v.strip() for v in requested_vehicles[0].split(',')]

    # Fetch available vehicle plate numbers
    cur.execute("""
        SELECT av.vehicle_name, array_agg(av.vehicle_plate) AS plates, v.image_link, v.brand
        FROM assigned_vehicles av
        JOIN vehicles v ON av.vehicle_name = v.vehiclename
        WHERE av.vehicle_name = ANY(%s) AND av.assigned_status = FALSE
        GROUP BY av.vehicle_name, v.image_link, v.brand
    """, (requested_vehicle_list,))

    available_vehicles = cur.fetchall()  # List of (vehicle_name, plates[], image_link, vehicle_brand)

    cur.close()
    conn.close()

    return render_template("review_request.html", 
                           driver=driver, 
                           requested_vehicles=requested_vehicle_list, 
                           available_vehicles=available_vehicles)

# Backend to assign or reject delegation of vehicles, redirects to this from review request form
@vendor_dashboard.route("/assign_vehicle", methods=["POST"])
def assign_vehicle():
    if 'email' not in session:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for("blueprints.login"))

    driver_email = request.form.get("driver_email")
    vehicle_name = request.form.get("vehicle_name")
    vehicle_brand = request.form.get("vehicle_brand")
    plate_number = request.form.get("plate_number")
    action = request.form.get("action")  

    if not driver_email:
        flash("Invalid request. Please try again.", "danger")
        return redirect(url_for("vendor_dashboard.vehicle_requests"))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if action == "approve":
            if not (vehicle_name and plate_number):
                flash("Invalid vehicle selection. Please select a valid vehicle.", "danger")
                return redirect(url_for("vendor_dashboard.review_request", driver_email=driver_email))

            # Check if the selected plate number is actually available
            cur.execute("""
                SELECT COUNT(*) FROM assigned_vehicles 
                WHERE vehicle_plate = %s AND assigned_status = FALSE
            """, (plate_number,))
            plate_available = cur.fetchone()[0]

            #In case if some other vendor assigns to someone in realtime
            if plate_available == 0:
                flash("Selected plate number is not available. Please try again.", "danger")
                return redirect(url_for("vendor_dashboard.review_request", driver_email=driver_email))

            # Marking the selected plate number as assigned in assigned_vehicles table
            cur.execute("""
                UPDATE assigned_vehicles 
                SET assigned_status = TRUE 
                WHERE vehicle_plate = %s
            """, (plate_number,))

            # Decrease availability count and also checking for edge case
            cur.execute("""
                UPDATE vehicles 
                SET availability = availability - 1 
                WHERE vehiclename = %s AND availability > 0
            """, (vehicle_name,))

            # Update the driver details
            cur.execute("""
                UPDATE drivers 
                SET vehicle_assigned = TRUE, 
                    vehicle_name = %s, 
                    vehicle_plate_number = %s, 
                    vehicle_brand = %s, 
                    request_status = 'approved'
                WHERE email = %s
            """, (vehicle_name, plate_number, vehicle_brand, driver_email))

            # Update vehicle request status to 'done'
            cur.execute("""
                UPDATE vehicle_requests 
                SET status = 'done' 
                WHERE driver_email = %s
            """, (driver_email,))

            flash("Vehicle successfully assigned to driver!", "success")

        elif action == "reject":
            # Delete the vehicle request
            cur.execute("""
                DELETE FROM vehicle_requests 
                WHERE driver_email = %s
            """, (driver_email,))

            # Reset request status to 'none'
            cur.execute("""
                UPDATE drivers 
                SET request_status = 'none'
                WHERE email = %s
            """, (driver_email,))

            flash("Vehicle request rejected.", "warning")

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("vendor_dashboard.vehicle_requests"))  

# Shows the vehicles assigned to the drivers
@vendor_dashboard.route("/active_vehicles")
def active_vehicles():
    if 'email' not in session:
        return redirect(url_for("blueprints.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all the vehicles that are assigned 
    cur.execute("""
        SELECT d.full_name, d.email, d.driver_image, d.license_image, 
               d.vehicle_name, d.vehicle_plate_number, d.vehicle_brand,
               v.image_link FROM drivers d
        JOIN vehicles v ON d.vehicle_name = v.vehiclename
        WHERE d.vehicle_assigned = TRUE
    """)
    
    active_drivers = cur.fetchall() 

    cur.close()
    conn.close()

    return render_template("active_vehicles.html", active_drivers=active_drivers)

# Allows the vendor to remove vehicles assigned
@vendor_dashboard.route("/remove_access", methods=["POST"])
def remove_access():
    if 'email' not in session:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for("blueprints.login"))

    driver_email = request.form.get("driver_email")

    if not driver_email:
        flash("Invalid request.", "danger")
        return redirect(url_for("vendor_dashboard.active_vehicles"))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch the assigned vehicle details
        cur.execute("""
            SELECT vehicle_name, vehicle_plate_number 
            FROM drivers 
            WHERE email = %s AND vehicle_assigned = TRUE
        """, (driver_email,))
        
        vehicle = cur.fetchone()

        if not vehicle:
            flash("No active vehicle assigned to this driver.", "warning")
            return redirect(url_for("vendor_dashboard.active_vehicles"))

        vehicle_name, plate_number = vehicle

        # Mark the vehicle as available again
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
        """, (driver_email,))

        conn.commit()
        flash("Vehicle access revoked successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("vendor_dashboard.active_vehicles"))

