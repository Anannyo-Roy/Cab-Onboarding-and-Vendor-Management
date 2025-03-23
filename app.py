from flask import Flask, render_template
from blueprints.routes import auth_bp
from blueprints.driver_dashboard import driver_dashboard
from blueprints.vendor_dashboard import vendor_dashboard
from db import create_table

app = Flask(__name__)
app.secret_key = "supersecretkey"

create_table()

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(driver_dashboard, url_prefix="/driver")
app.register_blueprint(vendor_dashboard, url_prefix="/vendor")

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
