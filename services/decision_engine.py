from models.settings import Settings
from ml.predictor import MLPredictor

class DecisionEngine:
    def __init__(self):
        self.predictor = MLPredictor()
        
    def analyze_vehicle(self, vehicle):
        # 1. Get ML Prediction (Reference only)
        vehicle_dict = {
            'tahun_perolehan': vehicle.tahun_perolehan,
            'harga_perolehan': vehicle.harga_perolehan,
            'kondisi_saat_ini': vehicle.kondisi_saat_ini,
            'jarak_tempuh': vehicle.jarak_tempuh,
            'jenis': vehicle.jenis
        }
        
        # ML Prediction as reference (will be overridden by adjusted book value)
        predicted_value = self.predictor.predict(vehicle_dict)
        
        # 2. Rule Based Evaluation (PMK Standard)
        settings = Settings.query.first()
        if not settings:
            settings = Settings() # Defaults
            
        reasons = []
        is_layak = False
        score = 0
        
        import datetime
        from dateutil.relativedelta import relativedelta # Need to make sure dateutil is available or use timedelta
        
        current_date = datetime.date.today()
        current_year = current_date.year
        vehicle_age = current_year - vehicle.tahun_perolehan
        min_age = settings.min_umur_lelang or 7
        econ_age = 10 # Batas usia ekonomis user request
        
        # Calculate Book Value (Straight Line with Residual Value)
        useful_life = settings.depreciation_life or 8
        residual_rate = 0.10  # 10% residual/salvage value for fully depreciated assets
        
        # Value = Cost * (1 - Age/Life), with minimum residual value
        depreciation_factor = max(0, 1 - (vehicle_age / useful_life))
        
        if depreciation_factor <= 0:
            # Fully depreciated - use residual value (10% of original cost)
            book_value = vehicle.harga_perolehan * residual_rate
        else:
            # Standard depreciation
            book_value = vehicle.harga_perolehan * depreciation_factor
        
        # Calculate Annual Repair Cost (Last 12 Months Maintenance + Active Damages)
        one_year_ago = current_date - datetime.timedelta(days=365)
        
        annual_maint = 0
        for m in vehicle.maintenances:
            m_date = m.tanggal
            if isinstance(m_date, datetime.datetime):
                m_date = m_date.date()
            if m_date >= one_year_ago:
                annual_maint += m.biaya
                
        active_damage_cost = sum(d.biaya_perbaikan for d in vehicle.damages if d.status != 'Selesai')
        total_annual_cost = annual_maint + active_damage_cost
        
        # Threshold 20% of Book Value
        cost_threshold = 0.20 * book_value
        is_uneconomical = total_annual_cost >= cost_threshold and total_annual_cost > 0

        # Calculate Condition automatically based on damages
        berat_count = sum(1 for d in vehicle.damages if d.tingkat_kerusakan == 'Berat' and d.status != 'Selesai')
        sedang_count = sum(1 for d in vehicle.damages if d.tingkat_kerusakan == 'Sedang' and d.status != 'Selesai')
        ringan_count = sum(1 for d in vehicle.damages if d.tingkat_kerusakan == 'Ringan' and d.status != 'Selesai')
        
        calculated_condition = 'Baik'
        if berat_count >= 1:
            calculated_condition = 'Rusak Berat'
        elif sedang_count >= 1:  # Changed: even 1 Sedang makes it Rusak Ringan
            calculated_condition = 'Rusak Ringan'
        elif ringan_count >= 1:  # NEW: handle Ringan damage
            calculated_condition = 'Rusak Ringan'
        vehicle.kondisi_saat_ini = calculated_condition

        # Apply Condition Adjustment to Book Value (PMK Standard)
        if calculated_condition == 'Rusak Berat':
            condition_factor = 0.50  # 50% dari nilai buku
        elif calculated_condition == 'Rusak Ringan':
            condition_factor = 0.75  # 75% dari nilai buku
        else:  # Baik
            condition_factor = 1.00  # 100% dari nilai buku
        
        adjusted_value = book_value * condition_factor
        
        # Store Book Value and Adjusted Value as prediction
        vehicle.nilai_buku = book_value
        vehicle.prediksi_nilai_jual = adjusted_value  # Use adjusted value as main prediction
        
        # Calculate Auction Limit (80% standar, range 50-80%)
        # PMK: Limit lelang biasanya 50-80% dari nilai taksir
        limit_lelang_standard = adjusted_value * 0.80  # 80% sebagai default
        limit_lelang_minimum = adjusted_value * 0.50  # 50% sebagai batas bawah
        
        # Set the standard limit (80%)
        vehicle.limit_lelang = limit_lelang_standard

        # Logic Flow
        # Rule 1: Age Check < 7
        if vehicle_age < min_age:
            # Underage (Normally Rejected, unless Critical Exception)
            if calculated_condition == 'Rusak Berat':
                # Special Case: Total Loss (Exception PMK)
                is_layak = True 
                score = 100
                reasons.append(f"Layak Lelang (Pengecualian): Usia {vehicle_age} th (< {min_age}). Kondisi Rusak Berat.")
            elif is_uneconomical:
                 # Special Case: High Repair Cost
                 is_layak = True
                 score = 90
                 val_str = "NOL" if book_value <= 0 else f"Rp {book_value:,.0f}"
                 reasons.append(f"Layak Lelang (Pengecualian): Usia {vehicle_age} th. Biaya (Rp {total_annual_cost:,.0f}) > 20% Nilai Buku ({val_str}).")
            else:
                is_layak = False
                score = 0
                reasons.append(f"Belum memenuhi syarat usia (Umur: {vehicle_age} th, Min: {min_age} th).")
        else:
            # Age Eligible (>= 7)
            reasons.append(f"Usia {vehicle_age} tahun.")
            
            # Priority 1: Age > 10
            if vehicle_age > econ_age:
                is_layak = True
                score = 95
                reasons.append("Telah melewati batas usia pakai ekonomis (>10 th).")
            
            # Priority 2: Uneconomical
            if is_uneconomical:
                is_layak = True
                score = max(score, 90) # At least 90
                val_str = "NOL" if book_value <= 0 else f"Rp {book_value:,.0f}"
                reasons.append(f"Tidak ekonomis: Est. Biaya (Rp {total_annual_cost:,.0f}) > 20% Nilai Buku ({val_str}).")

            # Priority 3: Condition
            if calculated_condition == 'Rusak Berat':
                is_layak = True
                score = 100 # Override to max
                reasons.append("Kondisi Rusak Berat.")
            elif calculated_condition == 'Rusak Ringan':
                if score < 90:
                     is_layak = True
                     score = max(score, 80)
                     reasons.append("Kondisi Rusak Ringan.")
            
            # Fallback
            if not is_layak:
                 reasons.append("Kondisi Baik & Masih Ekonomis.")
                 score = 20

        vehicle.rekomendasi_lelang = 'Layak Lelang' if is_layak else 'Tidak Layak'
        vehicle.skor_kelayakan = score
        vehicle.alasan_rekomendasi = " ".join(reasons)
        
        # Set timestamp when analysis is done
        vehicle.last_analyzed = datetime.datetime.now()
        
        return vehicle
