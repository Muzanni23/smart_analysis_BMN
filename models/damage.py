from datetime import datetime
from . import db

class Damage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    deskripsi = db.Column(db.Text, nullable=False)
    tingkat_kerusakan = db.Column(db.String(20), nullable=False) # Ringan, Sedang, Berat
    biaya_perbaikan = db.Column(db.Float, default=0.0)
    pelapor = db.Column(db.String(50), nullable=True) # Nama Pelapor/Driver
    status = db.Column(db.String(20), default='Belum Diperbaiki') # Belum Diperbaiki, Dalam Perbaikan, Selesai
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d'),
            'deskripsi': self.deskripsi,
            'tingkat': self.tingkat_kerusakan,
            'biaya': self.biaya_perbaikan,
            'status': self.status
        }
