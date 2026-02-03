import pandas as pd
from models import db
from models.vehicle import Vehicle
from io import BytesIO

class ExcelService:
    def import_vehicles(self, file_storage):
        try:
            # Validate file type
            filename = file_storage.filename if hasattr(file_storage, 'filename') else ''
            if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
                return False, "Format file tidak didukung. Gunakan file Excel (.xlsx atau .xls)"
            
            df = pd.read_excel(file_storage)
            
            # Expected columns: Plat, Jenis, Merk, Tipe, Tahun, Harga, Kondisi, KM
            # Map columns loosely
            
            count = 0
            for _, row in df.iterrows():
                # Fill NaN values before processing
                row = row.fillna({
                    'Plat Nomor': '',
                    'Plat': '',
                    'Jenis': 'Mobil',
                    'Merk': 'Toyota',
                    'Tipe': '-',
                    'Tahun': 2020,
                    'Harga': 0,
                    'Kondisi': 'Baik',
                    'KM': 0
                })
                
                plat = row.get('Plat Nomor') or row.get('Plat')
                if not plat or plat == '': 
                    continue
                
                # Check exist
                veh = Vehicle.query.filter_by(plat_no=str(plat)).first()
                if not veh:
                    veh = Vehicle(plat_no=str(plat))
                
                # Set all fields with safe defaults
                veh.jenis = str(row.get('Jenis', 'Mobil'))
                veh.merk = str(row.get('Merk', 'Toyota'))
                veh.tipe = str(row.get('Tipe', '-'))
                
                # Handle numeric fields
                tahun_val = row.get('Tahun', 2020)
                veh.tahun_perolehan = int(float(tahun_val)) if tahun_val else 2020
                
                harga_val = row.get('Harga', 0)
                veh.harga_perolehan = float(harga_val) if harga_val else 0.0
                
                veh.kondisi_saat_ini = str(row.get('Kondisi', 'Baik'))
                
                km_val = row.get('KM', 0)
                veh.jarak_tempuh = int(float(km_val)) if km_val else 0
                
                db.session.add(veh)
                count += 1
            
            db.session.commit()
            return True, f"Berhasil import {count} data."
        except Exception as e:
            return False, str(e)

    def export_analysis(self):
        vehicles = Vehicle.query.all()
        data = []
        for v in vehicles:
            data.append({
                'Plat No': v.plat_no,
                'Jenis': v.jenis,
                'Merk/Tipe': f"{v.merk} {v.tipe}",
                'Tahun': v.tahun_perolehan,
                'Harga Awal': v.harga_perolehan,
                'Kondisi': v.kondisi_saat_ini,
                'Prediksi Nilai': v.prediksi_nilai_jual,
                'Rekomendasi': v.rekomendasi_lelang,
                'Skor': v.skor_kelayakan,
                'Alasan': v.alasan_rekomendasi
            })
            
        return self._create_excel(data, 'Analisis')
        
    def export_auction_list(self, vehicles_data):
        # vehicles_data is list of dicts prepared by controller
        return self._create_excel(vehicles_data, 'Layak Lelang')
        
    def export_vehicle_history(self, timeline_data):
        # timeline_data is list of dicts
        return self._create_excel(timeline_data, 'Riwayat Kendaraan')
        
    def _create_excel(self, data, sheet_name):
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)
        return output
