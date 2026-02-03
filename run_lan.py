from app import app, db
import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    ip_address = get_ip()
    port = 5000
    
    print("\n" + "="*50)
    print(f" APLIKASI SMART BMN BERJALAN")
    print("="*50)
    print(f" Akses Lokal (Laptop ini):  http://127.0.0.1:{port}")
    print(f" Akses LAN (Teman Kantor):  http://{ip_address}:{port}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)

