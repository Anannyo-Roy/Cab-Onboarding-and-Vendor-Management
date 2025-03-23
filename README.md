 Cab Onboarding and Vendor Management Website

This is a Flask-based **Cab Onboarding and Vendor Management System** that streamlines the process of **driver onboarding**, **vehicle assignments**, and **vendor management**. 

- **Drivers** can register, upload their license details, request vehicles, and view assigned vehicles.  
- **Vendors** can register, onboard drivers, approve/reject vehicle requests, and manage assigned vehicles.  

**Features**
1. Authentication :
  User roles: **Driver** and **Vendor**  
  Secure login and registration using **Flask-Bcrypt**  
  Session-based authentication  

2. Driver Dashboard
  Profile management and image uploads  
  License and vehicle type selection  
  Request vehicles from vendors  
  View assigned vehicles and release them  

3. Vendor Dashboard
  Register vendors with business details  
  Approve/reject driver vehicle requests  
  Assign available vehicles to drivers  
  View active assigned vehicles  
  Remove vehicle access  

Tech Stack
- Backend: Flask (Blueprints for modular structure)  
- Database: PostgreSQL  
- Frontend: HTML, Bootstrap, CSS  
- Security: Flask-Bcrypt for password hashing  
- File Storage: Local directory for image uploads  

For the Dummy Database Use these to replace the function in db.py :

def get_db_connection():
    return psycopg2.connect(
        dbname="defaultdb",
        user="avnadmin",
        password="AVNS_33TSZRdY-oSeRa7rbrN",
        host="maindb-maindb.f.aivencloud.com",
        port="15289",
        sslmode="require"
    )
