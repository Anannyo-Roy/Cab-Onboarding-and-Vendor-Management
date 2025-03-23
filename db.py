import psycopg2

def get_db_connection():
    #Change these when running
    return psycopg2.connect(
        dbname="dbname",
        user="user",
        password="password"
        host="host",
        port="15289",
        sslmode="require"
    )

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create Drivers Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        email VARCHAR(100) PRIMARY KEY,
        full_name VARCHAR(100),
        hashed_password TEXT NOT NULL,
        phone VARCHAR(15) UNIQUE NOT NULL,
        license_number VARCHAR(50) UNIQUE,
        vehicle_type VARCHAR(50),
        driver_image TEXT,
        license_image TEXT,
        vehicle_assigned BOOLEAN DEFAULT FALSE, -- Changed to BOOLEAN
        vehicle_name TEXT, -- New column for assigned vehicle name
        vehicle_plate_number VARCHAR(50) UNIQUE, -- New column for assigned vehicle plate
        vehicle_brand TEXT, -- New column for assigned vehicle brand
        request_status VARCHAR(10) CHECK (request_status IN ('none', 'sent', 'approved')) DEFAULT 'none'
    );
    """)


    # Vendors table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        email VARCHAR(100) PRIMARY KEY,
        full_name VARCHAR(100),
        hashed_password TEXT NOT NULL,
        phone VARCHAR(15) UNIQUE NOT NULL,
        business_license VARCHAR(50) UNIQUE,
        vendor_image TEXT,  -- Path for vendor profile image
        business_license_image TEXT,  -- Path for business license image
        vendor_level VARCHAR(10) CHECK (vendor_level IN ('super', 'sub')) NOT NULL,  -- Vendor level can be 'super' or 'sub'
        registration_complete BOOLEAN DEFAULT FALSE  -- Indicates if registration is completed
    );
    """)


    # Create Vehicles Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id SERIAL PRIMARY KEY,
        name TEXT GENERATED ALWAYS AS (vehiclename || ' ' || brand) STORED,
        vehiclename TEXT NOT NULL,
        brand TEXT NOT NULL,
        type TEXT CHECK (type IN ('sedan', 'suv', 'hatchback', 'bike')) NOT NULL,
        image_link TEXT NOT NULL,
        availability INT NULL
    );
    """)

    # Create Vehicle Requests Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_requests (
        id SERIAL PRIMARY KEY,
        driver_email VARCHAR(100) NOT NULL,
        requested_vehicles TEXT NOT NULL,
        status VARCHAR(10) CHECK (status IN ('pending', 'done')) DEFAULT 'pending',
        FOREIGN KEY (driver_email) REFERENCES drivers(email) ON DELETE CASCADE
    );
    """)

    # Create Assigned Vehicles Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assigned_vehicles (
        id SERIAL PRIMARY KEY,
        vehicle_name TEXT NOT NULL,
        vehicle_plate VARCHAR(50) UNIQUE NOT NULL,
        assigned_status BOOLEAN DEFAULT FALSE
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
