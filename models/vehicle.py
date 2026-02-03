from datetime import datetime
from . import db

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plat_no = db.Column(db.String(20), unique=True, nullable=False)
    jenis = db.Column(db.String(50), nullable=False) # Mobil, Motor, Truk
    merk = db.Column(db.String(50), nullable=False)
    tipe = db.Column(db.String(50), nullable=False)
    tahun_perolehan = db.Column(db.Integer, nullable=False)
    harga_perolehan = db.Column(db.Float, nullable=False)
    kondisi_saat_ini = db.Column(db.String(20), nullable=False) # Baik, Rusak Ringan, Rusak Berat
    
    # User Info
    pengguna_saat_ini = db.Column(db.String(100), nullable=True)
    pejabat = db.Column(db.String(100), nullable=True)
    
    # ML & Analysis Fields
    jarak_tempuh = db.Column(db.Integer, nullable=True, default=0) # KM
    nilai_buku = db.Column(db.Float, nullable=True) # Nilai penyusutan
    
    # Prediction Results
    prediksi_nilai_jual = db.Column(db.Float, nullable=True)
    limit_lelang = db.Column(db.Float, nullable=True)  # Limit harga lelang (50-80% dari estimasi)
    rekomendasi_lelang = db.Column(db.String(20), nullable=True) # Layak / Tidak
    skor_kelayakan = db.Column(db.Float, nullable=True)
    alasan_rekomendasi = db.Column(db.Text, nullable=True)
    last_analyzed = db.Column(db.DateTime, nullable=True)

    maintenances = db.relationship('Maintenance', backref='vehicle', lazy=True, cascade="all, delete-orphan")
    damages = db.relationship('Damage', backref='vehicle', lazy=True, cascade="all, delete-orphan")
    usage_history = db.relationship('UsageHistory', backref='vehicle', lazy=True, cascade="all, delete-orphan")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plat_no': self.plat_no,
            'jenis': self.jenis,
            'merk': self.merk,
            'tipe': self.tipe,
            'tahun': self.tahun_perolehan,
            'harga_awal': self.harga_perolehan,
            'kondisi': self.kondisi_saat_ini,
            'prediksi': self.prediksi_nilai_jual,
            'rekomendasi': self.rekomendasi_lelang
        }
