from . import db

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Rules thresholds
    max_biaya_perawatan_pct = db.Column(db.Float, default=70.0) # Jika biaya > 70% harga awal
    min_umur_lelang = db.Column(db.Integer, default=7) # Min 7 tahun (PMK 165/2021)
    depreciation_life = db.Column(db.Integer, default=8) # Masa manfaat 8 tahun (Kelompok 2)
    wajib_lelang_kondisi = db.Column(db.String(50), default='Rusak Berat')
    
    updated_at = db.Column(db.DateTime, nullable=True)
