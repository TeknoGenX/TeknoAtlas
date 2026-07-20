import sqlite3
import json
import os
from werkzeug.security import generate_password_hash

DATABASE_PATH = 'data/teknoatlas.db'
TECH_DATA_JSON = 'data/tech_data.json'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Buat direktori data jika belum ada
    os.makedirs('data', exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tabel Users untuk Authentication & Authorization
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # 2. Tabel Countries untuk profil teknologi & data dari API
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            cca3 TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            maturity INTEGER NOT NULL,
            code TEXT,
            desc TEXT,
            full_description TEXT,
            innovation_hubs TEXT,
            challenges TEXT,
            universities TEXT,
            tech_sectors TEXT
        )
    ''')
    
    conn.commit()
    
    # Seed default users jika belum ada
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default Admin: admin / admin123
        admin_pass = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ('admin', admin_pass, 'admin'))
        
        # Default User: user / user123
        user_pass = generate_password_hash('user123')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ('user', user_pass, 'user'))
        conn.commit()
        print("[DB] Default users seeded (admin/admin123, user/user123)")

    # Seed countries dari tech_data.json jika belum ada
    cursor.execute("SELECT COUNT(*) FROM countries")
    if cursor.fetchone()[0] == 0 and os.path.exists(TECH_DATA_JSON):
        try:
            with open(TECH_DATA_JSON, 'r') as f:
                tech_data = json.load(f)
                
            for cca3, data in tech_data.items():
                cursor.execute('''
                    INSERT INTO countries (
                        cca3, name, maturity, code, desc, full_description, 
                        innovation_hubs, challenges, universities, tech_sectors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cca3.upper(),
                    data.get('name'),
                    data.get('maturity'),
                    data.get('code'),
                    data.get('desc'),
                    data.get('full_description'),
                    json.dumps(data.get('innovation_hubs', [])),
                    json.dumps(data.get('challenges', [])),
                    json.dumps(data.get('universities', [])),
                    json.dumps(data.get('tech_sectors', {}))
                ))
            conn.commit()
            print(f"[DB] Seeded {len(tech_data)} countries from JSON file.")
        except Exception as e:
            print(f"[DB] Error seeding countries: {e}")
            conn.rollback()
            
    conn.close()

# Helper functions untuk CRUD Countries
def get_all_countries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries")
    rows = cursor.fetchall()
    conn.close()
    
    countries_dict = {}
    for r in rows:
        countries_dict[r['cca3']] = {
            'name': r['name'],
            'maturity': r['maturity'],
            'code': r['code'],
            'desc': r['desc'],
            'full_description': r['full_description'],
            'innovation_hubs': json.loads(r['innovation_hubs']) if r['innovation_hubs'] else [],
            'challenges': json.loads(r['challenges']) if r['challenges'] else [],
            'universities': json.loads(r['universities']) if r['universities'] else [],
            'tech_sectors': json.loads(r['tech_sectors']) if r['tech_sectors'] else {}
        }
    return countries_dict

def get_country(cca3):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries WHERE cca3 = ?", (cca3.upper(),))
    r = cursor.fetchone()
    conn.close()
    if r:
        return {
            'cca3': r['cca3'],
            'name': r['name'],
            'maturity': r['maturity'],
            'code': r['code'],
            'desc': r['desc'],
            'full_description': r['full_description'],
            'innovation_hubs': json.loads(r['innovation_hubs']) if r['innovation_hubs'] else [],
            'challenges': json.loads(r['challenges']) if r['challenges'] else [],
            'universities': json.loads(r['universities']) if r['universities'] else [],
            'tech_sectors': json.loads(r['tech_sectors']) if r['tech_sectors'] else {}
        }
    return None

def insert_country(
    cca3,
    name,
    maturity,
    code,
    desc,
    full_description,
    hubs,
    challenges,
    universities,
    sectors
):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cca3 = cca3.strip().upper()
        name = name.strip()
        code = code.strip().upper()
        maturity = int(maturity)

        # Cek apakah kode negara sudah digunakan
        cursor.execute(
            "SELECT cca3 FROM countries WHERE cca3 = ?",
            (cca3,)
        )

        if cursor.fetchone():
            return False, f"Negara dengan kode ISO3 {cca3} sudah ada."

        cursor.execute('''
            INSERT INTO countries (
                cca3,
                name,
                maturity,
                code,
                "desc",
                full_description,
                innovation_hubs,
                challenges,
                universities,
                tech_sectors
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cca3,
            name,
            maturity,
            code,
            desc,
            full_description,
            json.dumps(hubs or [], ensure_ascii=False),
            json.dumps(challenges or [], ensure_ascii=False),
            json.dumps(universities or [], ensure_ascii=False),
            json.dumps(sectors or {}, ensure_ascii=False)
        ))

        conn.commit()
        return True, None

    except (sqlite3.Error, TypeError, ValueError) as error:
        conn.rollback()
        print(f"[DB] Gagal menambahkan negara: {error}")
        return False, str(error)

    finally:
        conn.close()
def update_country(cca3, name, maturity, code, desc, full_description, hubs, challenges, universities, sectors):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE countries SET
                name = ?, maturity = ?, code = ?, desc = ?, full_description = ?, 
                innovation_hubs = ?, challenges = ?, universities = ?, tech_sectors = ?
            WHERE cca3 = ?
        ''', (
            name, maturity, code, desc, full_description,
            json.dumps(hubs), json.dumps(challenges), json.dumps(universities), json.dumps(sectors),
            cca3.upper()
        ))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

def delete_country(cca3):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM countries WHERE cca3 = ?", (cca3.upper(),))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()
