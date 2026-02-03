from datetime import datetime
from . import db

class UsageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=True)
    
    driver_name = db.Column(db.String(100), nullable=False)
    pejabat_name = db.Column(db.String(100), nullable=False)
    jabatan = db.Column(db.String(100), nullable=False)
    
    keperluan = db.Column(db.Text, nullable=False)
    tujuan = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
