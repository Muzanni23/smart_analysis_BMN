# Panduan Deployment Smart BMN (Cloudflare Tunnel)

Dokumen ini telah disesuaikan untuk konfigurasi Cloudflare Tunnel Anda (`app.techsmartapps.com` -> `http://flask:8000`).

## Prasyarat
1.  **Server VPS** dengan akses SSH.
2.  **Cloudflare Tunnel** sudah aktif (seperti di screenshot Anda).
3.  **Docker & Docker Compose** terinstall di server.

---

## Tahap 1: Persiapan di Server VPS

Masuk ke server Anda via SSH.

### 1. Upload File Aplikasi
Upload semua file project (atau `git clone`) ke server, misal ke folder `~/smart_bmn`.

### 2. Konfigurasi Network (PENTING)
Agar Cloudflare Tunnel bisa mengakses service `flask`, mereka idealnya berada di network Docker yang sama.

**Opsi A: Cloudflare Tunnel berjalan di Docker (Recommended)**
Cek nama network container cloudflared Anda:
```bash
docker network ls
```
Jika Anda punya network khusus (misal `homelab_net`), edit file `docker-compose.yml` di server:
1.  Buka `docker-compose.yml`.
2.  Ubah bagian `networks`:
    ```yaml
    networks:
      default:
        external:
          name: homelab_net  <-- Ganti dengan nama network tunnel Anda
    ```

**Opsi B: Cloudflare Tunnel berjalan di Host (Service Linux)**
Tidak perlu ubah apa-apa. `docker-compose.yml` saya sudah mengekspos port `8000`. Pastikan Tunnel Anda mengarah ke `http://localhost:8000` atau `http://127.0.0.1:8000`.
*(Catatan: Screenshot Anda menunjukkan `http://flask:8000`, yang mengindikasikan Opsi A lebih mungkin. Jika Opsi B gagal, coba ubah config Tunnel di dashboard Cloudflare ke `localhost:8000`).*

---

## Tahap 2: Menjalankan Aplikasi

Di dalam folder project, jalankan:

```bash
docker compose up -d --build
```

Ini akan membuat container bernama `smart_bmn_app` dengan service name `flask`.

---

## Tahap 3: Verifikasi

1.  Cek status container:
    ```bash
    docker compose ps
    ```
2.  Buka browser: `https://app.techsmartapps.com`
3.  Jika settingan Tunnel sudah benar mengarah ke `http://flask:8000` dan mereka satu network, aplikasi akan muncul.

---

## Troubleshooting Cloudflare Tunnel

Jika muncul **502 Bad Gateway**:
1.  Pastikan container `flask` dan container tunnel ada di satu network.
    *   Coba `docker network connect [nama_network_tunnel] smart_bmn_app`
2.  Atau, ubah konfigurasi Tunnel di Dashboard Cloudflare:
    *   Ganti Service dari `http://flask:8000` menjadi `http://[IP_LOKAL_SERVER]:8000`.
