from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
from flask_login import login_required, current_user
from models import db
from models.vehicle import Vehicle
from models.maintenance import Maintenance
from models.settings import Settings
from services.excel_service import ExcelService
from services.decision_engine import DecisionEngine
from ml.trainer import MLTrainer
import json
import os

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def dashboard():
    total_vehicles = Vehicle.query.count()
    layak_vehicles = Vehicle.query.filter_by(rekomendasi_lelang='Layak Lelang').count()
    
    # Count damaged vehicles
    damaged_vehicles = Vehicle.query.filter(
        (Vehicle.kondisi_saat_ini == 'Rusak Ringan') | 
        (Vehicle.kondisi_saat_ini == 'Rusak Berat')
    ).count()
    
    # Condition distribution for bar chart
    baik_count = Vehicle.query.filter_by(kondisi_saat_ini='Baik').count()
    rusak_ringan_count = Vehicle.query.filter_by(kondisi_saat_ini='Rusak Ringan').count()
    rusak_berat_count = Vehicle.query.filter_by(kondisi_saat_ini='Rusak Berat').count()
    condition_data = [baik_count, rusak_ringan_count, rusak_berat_count]
    
    # Chart Data
    # 1. Status Ratio
    status_data = [layak_vehicles, total_vehicles - layak_vehicles]
    
    # 2. ML Performance
    try:
        with open('ml/saved_models/best_model.json', 'r') as f:
            content = json.load(f)
            ml_metrics = content.get('metrics', {})
            # Sanitize NaN
            import math
            for m in ml_metrics:
                for k in ml_metrics[m]:
                    if isinstance(ml_metrics[m][k], float) and math.isnan(ml_metrics[m][k]):
                        ml_metrics[m][k] = 0.0
    except:
        ml_metrics = None

    vehicles = Vehicle.query.order_by(Vehicle.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           total=total_vehicles, 
                           layak=layak_vehicles,
                           damaged=damaged_vehicles,
                           status_data=status_data,
                           condition_data=condition_data,
                           ml_metrics=ml_metrics,
                           recent_vehicles=vehicles)

@main.route('/vehicle/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(id):
    v = Vehicle.query.get_or_404(id)
    if request.method == 'POST':
        v.plat_no = request.form['plat']
        v.jenis = request.form['jenis']
        v.merk = request.form['merk']
        v.tipe = request.form['tipe']
        v.tahun_perolehan = int(request.form['tahun'])
        v.harga_perolehan = float(request.form['harga'])
        v.kondisi_saat_ini = request.form['kondisi']
        v.jarak_tempuh = int(request.form['km'])
        
        # New Fields
        v.pengguna_saat_ini = request.form.get('pengguna')
        v.pejabat = request.form.get('pejabat')
        
        from services.decision_engine import DecisionEngine
        de = DecisionEngine()
        de.analyze_vehicle(v)
        
        try:
            db.session.commit()
            flash('Data kendaraan diperbarui.', 'success')
            return redirect(url_for('main.vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal update: {str(e)}', 'danger')
            
    return render_template('edit_vehicle.html', v=v)

@main.route('/vehicle/delete/<int:id>', methods=['POST'])
@login_required
def delete_vehicle(id):
    v = Vehicle.query.get_or_404(id)
    try:
        db.session.delete(v)
        db.session.commit()
        flash('Data kendaraan dihapus.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus: {str(e)}', 'danger')
    return redirect(url_for('main.vehicles'))

@main.route('/vehicles', methods=['GET', 'POST'])
@login_required
def vehicles():
    if request.method == 'POST':
        # Simple Add Vehicle
        v = Vehicle(
            plat_no=request.form['plat'],
            jenis=request.form['jenis'],
            merk=request.form['merk'],
            tipe=request.form['tipe'],
            tahun_perolehan=int(request.form['tahun']),
            harga_perolehan=float(request.form['harga']),
            kondisi_saat_ini=request.form['kondisi'],
            jarak_tempuh=int(request.form['km']),
            pengguna_saat_ini=request.form.get('pengguna'),
            pejabat=request.form.get('pejabat')
        )
        try:
            db.session.add(v)
            db.session.commit()
            
            # Trigger single analysis
            de = DecisionEngine()
            de.analyze_vehicle(v)
            db.session.commit()
            
            flash('Kendaraan ditambahkan', 'success')
        except Exception as e:
            db.session.rollback()
            if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(e):
                flash(f'Gagal: Plat Nomor {v.plat_no} sudah terdaftar.', 'danger')
            else:
                flash(f'Gagal menambahkan kendaraan: {str(e)}', 'danger')
        
        return redirect(url_for('main.vehicles'))
        
    all_vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=all_vehicles)

@main.route('/damaged_vehicles')
@login_required
def damaged_vehicles():
    vehicles = Vehicle.query.filter(
        (Vehicle.kondisi_saat_ini == 'Rusak Ringan') | 
        (Vehicle.kondisi_saat_ini == 'Rusak Berat')
    ).all()
    return render_template('damaged_vehicles.html', vehicles=vehicles)

@main.route('/export_damaged')
@login_required
def export_damaged():
    import pandas as pd
    import io
    
    vehicles = Vehicle.query.filter(
        (Vehicle.kondisi_saat_ini == 'Rusak Ringan') |
        (Vehicle.kondisi_saat_ini == 'Rusak Berat')
    ).all()
    
    data = []
    for v in vehicles:
        data.append({
            'Plat Nomor': v.plat_no,
            'Jenis': v.jenis,
            'Merk': v.merk,
            'Tipe': v.tipe,
            'Tahun': v.tahun_perolehan,
            'Kondisi': v.kondisi_saat_ini,
            'Jarak Tempuh': v.jarak_tempuh,
            'Harga Perolehan': v.harga_perolehan,
            'Prediksi Nilai Jual': v.prediksi_nilai_jual,
            'Rekomendasi': v.rekomendasi_lelang,
            'Skor': v.skor_kelayakan
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Kendaraan Rusak')
    
    output.seek(0)
    return send_file(output, 
                     download_name=f'kendaraan_rusak_{datetime.now().strftime("%Y%m%d")}.xlsx',
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@main.route('/maintenance/<int:id>', methods=['GET', 'POST'])
@login_required
def add_maintenance(id):
    from models.damage import Damage
    from services.decision_engine import DecisionEngine
    
    v = Vehicle.query.get_or_404(id)
    
    if request.method == 'POST':
        damage_id = request.form.get('damage_id')
        jenis = request.form.get('jenis')
        
        # If linked to damage
        damage_record = None
        if damage_id and damage_id != 'None':
            damage_record = Damage.query.get(damage_id)
            if damage_record:
                damage_record.status = 'Selesai'
                if not jenis:
                    jenis = f"Perbaikan: {damage_record.deskripsi}"
        
        if not jenis:
            jenis = "Perawatan Rutin / Umum"

        biaya = float(request.form['biaya'])
        m = Maintenance(
            vehicle_id=id,
            damage_id=damage_record.id if damage_record else None,
            jenis_perawatan=jenis,
            biaya=biaya,
            keterangan=request.form.get('keterangan')
        )
        db.session.add(m)
        
        # Re-analyze vehicle
        de = DecisionEngine()
        de.analyze_vehicle(v)
        
        db.session.commit()
        flash('Data perawatan disimpan & status kerusakan diperbarui.', 'success')
        return redirect(url_for('main.vehicles'))
        
    return render_template('add_maintenance.html', v=v)

@main.route('/damage/<int:id>', methods=['GET', 'POST'])
@login_required
def add_damage(id):
    from models.damage import Damage
    from services.decision_engine import DecisionEngine
    
    v = Vehicle.query.get_or_404(id)
    
    if request.method == 'POST':
        d = Damage(
            vehicle_id=id,
            tanggal=datetime.strptime(request.form['tanggal'], '%Y-%m-%d').date(),
            deskripsi=request.form['deskripsi'],
            tingkat_kerusakan=request.form['tingkat'], # Ringan, Sedang, Berat
            biaya_perbaikan=float(request.form['biaya'] or 0),
            pelapor=request.form.get('pelapor'),
            status='Belum Diperbaiki'
        )
        db.session.add(d)
        
        # Auto-update status kendaraan via DecisionEngine
        de = DecisionEngine()
        de.analyze_vehicle(v)
        
        db.session.commit()
        flash('Laporan kerusakan disimpan. Status kendaraan diperbarui.', 'warning')
        return redirect(url_for('main.vehicles'))
        
    return render_template('add_damage.html', v=v, today=datetime.today().strftime('%Y-%m-%d'))

@main.route('/usage/<int:id>', methods=['GET', 'POST'])
@login_required
def add_usage(id):
    from models.usage import UsageHistory
    
    v = Vehicle.query.get_or_404(id)
    
    if request.method == 'POST':
        u = UsageHistory(
            vehicle_id=id,
            tanggal_mulai=datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%d').date(),
            driver_name=request.form['driver'],
            pejabat_name=request.form['pejabat'],
            jabatan=request.form['jabatan'],
            keperluan=request.form['keperluan'],
            tujuan=request.form['tujuan']
        )
        db.session.add(u)
        db.session.commit()
        flash('Riwayat pemakaian dicatat.', 'success')
        return redirect(url_for('main.vehicles'))
        
    return render_template('add_usage.html', v=v, today=datetime.today().strftime('%Y-%m-%d'))

@main.route('/import', methods=['POST'])
@login_required
def upload_excel():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.vehicles'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('main.vehicles'))
        
    svc = ExcelService()
    success, msg = svc.import_vehicles(file)
    if success:
        # Trigger Analysis for all vehicles (especially new ones)
        from services.decision_engine import DecisionEngine
        de = DecisionEngine()
        vehicles = Vehicle.query.all()
        for v in vehicles:
            de.analyze_vehicle(v)
        db.session.commit()
        
        flash(f"{msg}. Analisis kendaraan berhasil diperbarui.", 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('main.vehicles'))

@main.route('/export')
@login_required
def export_excel():
    svc = ExcelService()
    output = svc.export_analysis()
    return send_file(output, download_name='analisis_bmn.xlsx', as_attachment=True)

@main.route('/analyze')
@login_required
def analyze_all():
    vehicles = Vehicle.query.all()
    de = DecisionEngine()
    count = 0
    for v in vehicles:
        de.analyze_vehicle(v)
        count += 1
    db.session.commit()
    flash(f'{count} kendaraan dianalisis ulang.', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role != 'Admin':
        flash('Akses ditolak', 'danger')
        return redirect(url_for('main.dashboard'))
        
    s = Settings.query.first()
    if not s:
        s = Settings()
        db.session.add(s)
        
    if request.method == 'POST':
        s.max_biaya_perawatan_pct = float(request.form['max_biaya'])
        s.wajib_lelang_kondisi = request.form['kondisi_rusak']
        db.session.commit()
        flash('Pengaturan disimpan', 'success')
        
    return render_template('settings.html', settings=s)

@main.route('/retrain')
@login_required
def retrain():
    # Fetch data from DB
    import pandas as pd
    vehicles = Vehicle.query.all()
    if not vehicles:
        flash('Tidak ada data untuk training', 'warning')
        return redirect(url_for('main.dashboard'))
    
    data = [v.to_dict() for v in vehicles]
    df = pd.DataFrame(data)
    # Map for training
    # Ideally we need historical sales data ("Real Value"), but for now we simulate target
    # In real app, user would upload 'Sales History' separately
    # Here we mock the target based on depreciation formula for demonstration
    current_year = 2024
    df['nilai_pasar_real'] = df['harga_awal'] * (0.85 ** (current_year - df['tahun']))
    df['kondisi_saat_ini'] = df['kondisi']
    df['harga_perolehan'] = df['harga_awal']
    df['tahun_perolehan'] = df['tahun']
    df['jarak_tempuh'] = 10000 # Mock if missing
    
    trainer = MLTrainer()
    results = trainer.train_all(df=df)
    
    flash(f'Training Selesai! Best Model updated.', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/auction-recommendations')
@login_required
def auction_list():
    vehicles = Vehicle.query.filter_by(rekomendasi_lelang='Layak Lelang').all()
    # Add context (last user)
    results = []
    for v in vehicles:
        last_usage = sorted(v.usage_history, key=lambda x: x.tanggal_mulai, reverse=True)
        current_user_info = last_usage[0] if last_usage else None
        
        results.append({
            'vehicle': v,
            'current_user': current_user_info
        })
        
    return render_template('auction_list.html', results=results)

@main.route('/auction-recommendations/export')
@login_required
def export_auction_list():
    vehicles = Vehicle.query.filter_by(rekomendasi_lelang='Layak Lelang').all()
    data = []
    for v in vehicles:
        last_usage = sorted(v.usage_history, key=lambda x: x.tanggal_mulai, reverse=True)
        u = last_usage[0] if last_usage else None
        
        data.append({
            'Plat No': v.plat_no,
            'Jenis': v.jenis,
            'Merk/Tipe': f"{v.merk} {v.tipe}",
            'Tahun': v.tahun_perolehan,
            'Kondisi': v.kondisi_saat_ini,
            'Rekomendasi': v.rekomendasi_lelang,
            'Alasan': v.alasan_rekomendasi,
            'Driver Terakhir': u.driver_name if u else '-',
            'Pejabat Terakhir': u.pejabat_name if u else '-'
        })
        
    svc = ExcelService()
    output = svc.export_auction_list(data)
    return send_file(output, download_name='rekomendasi_lelang.xlsx', as_attachment=True)

@main.route('/vehicle/<int:id>/history')
@login_required
def vehicle_history(id):
    v = Vehicle.query.get_or_404(id)
    
    # Aggregate timeline
    timeline = []
    
    for m in v.maintenances:
        timeline.append({
            'date': m.tanggal,
            'type': 'Perawatan',
            'summary': m.jenis_perawatan,
            'cost': m.biaya,
            'details': m.keterangan,
            'user': '-'
        })
        
    for d in v.damages:
        timeline.append({
            'date': d.tanggal,
            'type': 'Kerusakan',
            'summary': f"{d.tingkat_kerusakan}: {d.deskripsi}",
            'cost': d.biaya_perbaikan,
            'details': f"Status: {d.status}",
            'user': d.pelapor or '-'
        })
        
    for u in v.usage_history:
        timeline.append({
            'date': u.tanggal_mulai,
            'type': 'Pemakaian',
            'summary': f"Tujuan: {u.tujuan}",
            'cost': 0,
            'details': f"Keperluan: {u.keperluan}",
            'user': f"{u.driver_name} / {u.pejabat_name}"
        })
        
    # Sort descending
    timeline.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('vehicle_history.html', vehicle=v, timeline=timeline)

@main.route('/vehicle/<int:id>/history/export')
@login_required
def export_vehicle_history(id):
    v = Vehicle.query.get_or_404(id)
    
    # Logic duplicated for export (Ideally refactor to service, but keeping inline for speed)
    data = []
    
    for m in v.maintenances:
        data.append({'Tanggal': m.tanggal, 'Tipe': 'Perawatan', 'Ringkasan': m.jenis_perawatan, 'Biaya': m.biaya, 'Detail': m.keterangan, 'User': '-'})
        
    for d in v.damages:
        data.append({'Tanggal': d.tanggal, 'Tipe': 'Kerusakan', 'Ringkasan': f"{d.tingkat_kerusakan}: {d.deskripsi}", 'Biaya': d.biaya_perbaikan, 'Detail': f"Status: {d.status}", 'User': d.pelapor})
        
    for u in v.usage_history:
        data.append({'Tanggal': u.tanggal_mulai, 'Tipe': 'Pemakaian', 'Ringkasan': f"Tujuan: {u.tujuan}", 'Biaya': 0, 'Detail': f"Keperluan: {u.keperluan}", 'User': f"{u.driver_name} / {u.pejabat_name}"})
        
    data.sort(key=lambda x: x['Tanggal'], reverse=True)
    
    svc = ExcelService()
    output = svc.export_vehicle_history(data)
    return send_file(output, download_name=f'riwayat_{v.plat_no}.xlsx', as_attachment=True)
