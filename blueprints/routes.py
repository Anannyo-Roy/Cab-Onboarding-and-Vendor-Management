from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2
from flask_bcrypt import Bcrypt
from db import get_db_connection

auth_bp = Blueprint('blueprints', __name__)  
bcrypt = Bcrypt()

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    role = request.args.get('role', 'driver')  
    session['role'] = role  # Store role in session

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # check based on role
        table = "vendors" if session['role'] == "vendor" else "drivers"
        cursor.execute(f"SELECT email, hashed_password FROM {table} WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        # Validate credentials
        if user and bcrypt.check_password_hash(user[1], password):  # user[1] is hashed_password
            session['email'] = user[0]  

            flash("Login successful!", "success")

            return redirect(url_for('vendor_dashboard.dashboard' if session['role'] == "vendor" else 'driver_dashboard.dashboard'))

        flash("Invalid email or password", "danger")

    return render_template("login.html") 



# Registration Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        phone = request.form['phone']
        role = request.form['role']  

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # if email or phone already exists then flash danger
            cursor.execute("SELECT email FROM drivers WHERE email = %s UNION SELECT email FROM vendors WHERE email = %s", (email, email))
            existing_email = cursor.fetchone()
            
            cursor.execute("SELECT phone FROM drivers WHERE phone = %s UNION SELECT phone FROM vendors WHERE phone = %s", (phone, phone))
            existing_phone = cursor.fetchone()

            if existing_email:
                flash("Email already exists. Please use a different email.", "danger")
                return render_template("register.html")

            if existing_phone:
                flash("Phone number already exists. Please use a different phone number.", "danger")
                return render_template("register.html")

            # Insert data 
            if role == 'driver':
                cursor.execute("""
                    INSERT INTO drivers (email, hashed_password, phone) 
                    VALUES (%s, %s, %s)
                """, (email, password, phone))
            elif role == 'vendor':
                cursor.execute("""
                    INSERT INTO vendors (email, hashed_password, phone) 
                    VALUES (%s, %s, %s)
                """, (email, password, phone))

            conn.commit()

            flash('Registration successful!', 'success')
            return redirect(url_for('blueprints.home'))  

        except psycopg2.Error as e:
            print(f"Database Error: {e}")  
            flash("An error occurred during registration. Please try again.", 'danger')

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')



# Dashboard Route
@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('driver_dashboard.html', username=session['username'])  
    return redirect(url_for('blueprints.home'))

# Logout Route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('blueprints.home'))

# Redirect to landing page
@auth_bp.route('/')
def home():
    return render_template('home.html')  
