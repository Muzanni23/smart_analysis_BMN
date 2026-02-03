from datetime import datetime
from . import db

class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    damage_id = db.Column(db.Integer, db.ForeignKey('damage.id'), nullable=True) # Linked Damage
    
    jenis_perawatan = db.Column(db.String(100), nullable=False) # Copied from Damage deskripsi or 'Service Berkala'
    biaya = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    keterangan = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to Damage
    # damage = db.relationship('Damage', backref='maintenances')
