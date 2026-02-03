from flask import Flask
from config import Config
from models import db, login_manager
from models.user import User
from models.vehicle import Vehicle
from models.damage import Damage
from models.usage import UsageHistory
from controllers.auth import auth, bcrypt
from controllers.main import main
import os

app = Flask(__name__)

# Health Check
@app.route('/health_check')
def health_check():
    return "Smart BMN Server is Running", 200

app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)

app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(main)

# Make datetime available in all templates for dynamic year
import datetime
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}


def create_dummy_data():
    if not User.query.first():
        # Create Admin
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(username='admin', email='admin@bmn.go.id', role='Admin', password=hashed_pw)
        
        # Create Operator
        op_pw = bcrypt.generate_password_hash('operator123').decode('utf-8')
        operator = User(username='operator', email='op@bmn.go.id', role='Operator', password=op_pw)
        
        # Create Pejabat
        pj_pw = bcrypt.generate_password_hash('pejabat123').decode('utf-8')
        pejabat = User(username='pejabat', email='pejabat@bmn.go.id', role='Pejabat Penilai', password=pj_pw)
        
        db.session.add(admin)
        db.session.add(operator)
        db.session.add(pejabat)
        
        # Create Dummy Vehicles
        v1 = Vehicle(plat_no='B 1234 CD', jenis='Mobil', merk='Toyota', tipe='Avanza', 
                     tahun_perolehan=2015, harga_perolehan=200000000, kondisi_saat_ini='Baik', jarak_tempuh=50000)
        v2 = Vehicle(plat_no='B 9999 XX', jenis='Mobil', merk='Mitsubishi', tipe='Pajero', 
                     tahun_perolehan=2010, harga_perolehan=450000000, kondisi_saat_ini='Rusak Berat', jarak_tempuh=150000)
        
        db.session.add(v1)
        db.session.add(v2)
        
        db.session.commit()
        print("Dummy data created!")

# Auto-setup for Production (Gunicorn) / Development
# This ensures tables exist even when not running via 'python app.py'
with app.app_context():
    db.create_all()
    # Check if we need dummy data (only if user table is empty)
    # We wrap in try-except in case of migration issues, though create_all handles most.
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if inspector.has_table("user"):
            if not User.query.first():
                create_dummy_data()
    except Exception as e:
        print(f"Auto-setup warning: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
