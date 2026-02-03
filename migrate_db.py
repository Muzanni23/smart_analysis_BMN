import sqlite3

def migrate():
    conn = sqlite3.connect('instance/smart_bmn.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE vehicle ADD COLUMN pengguna_saat_ini VARCHAR(100)")
        print("Added pengguna_saat_ini column")
    except sqlite3.OperationalError as e:
        print(f"Skipped pengguna_saat_ini: {e}")

    try:
        cursor.execute("ALTER TABLE vehicle ADD COLUMN pejabat VARCHAR(100)")
        print("Added pejabat column")
    except sqlite3.OperationalError as e:
        print(f"Skipped pejabat: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
