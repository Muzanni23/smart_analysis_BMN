# Smart Analysis BMN System

Sistem analisis aset kendaraan BMN menggunakan Artificial Intelligence (Machine Learning) untuk prediksi nilai pasar dan rekomendasi lelang.

## Persyaratan Sistem
- Python 3.8 atau lebih baru.
- Koneksi internet (untuk mengunduh library pertama kali).

## Cara Menjalankan (Langkah demi Langkah)

### 1. Persiapan Awal (Hanya sekali di awal)
Jika Anda baru memindahkan folder ini ke komputer baru, instal dulu library yang dibutuhkan:
```bash
pip install -r requirements.txt
```

### 2. Menjalankan Aplikasi
Buka terminal/command prompt di dalam folder ini, lalu ketik:
```bash
python app.py
```

### 3. Mengakses Dashboard
Setelah muncul tulisan `Running on http://127.0.0.1:5000`, buka browser (Chrome/Edge) dan kunjungi:
http://localhost:5000

## Fitur Utama
- **Dashboard**: Ringkasan total aset dan grafik kondisi.
- **Prediksi AI**: Estimasi harga jual aset berdasarkan Merk, Tipe, Umur, dan Kondisi.
- **Analisis**: Rekomendasi otomatis apakah aset sebaiknya dilelang atau dipertahankan.

## Catatan
- Database menggunakan SQLite (`instance/smart_analysis.db`).
- Model AI tersimpan di folder `ml/saved_models`.
- Jika ingin melatih ulang AI, klik tombol "Retrain AI" di dashboard.
