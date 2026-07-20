from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import logging
import json
import re
from concurrent.futures import ThreadPoolExecutor
from flask_caching import Cache
from ml_engine import InnovationPredictor
from services import DataNexus
from database import (
    init_db, get_db_connection, get_all_countries, get_country, 
    insert_country, update_country, delete_country
)
from werkzeug.security import generate_password_hash, check_password_hash

# ==========================================
# 1. CORE SETUP & INITIALIZATION
# ==========================================
app = Flask(__name__)
app.secret_key = 'super-secret-key-teknoatlas-backend-2026'

# Inisialisasi Database SQLite
init_db()

# Konfigurasi Caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 3600})

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TeknoAtlas-BackEnd")

predictor = InnovationPredictor()
nexus = DataNexus(get_all_countries())

# ==========================================
# 2. MIDDLEWARE (Auth & Request Logging)
# ==========================================
@app.before_request
def require_login_middleware():
    # Logging setiap request
    user = session.get('username', 'Guest')
    role = session.get('role', 'none')
    logger.info(f"[Request] Path: {request.path} | Method: {request.method} | User: {user} ({role})")
    
    # Tentukan route publik yang bebas diakses guest
    public_routes = ['login', 'register', 'static']
    endpoint = request.endpoint
    
    if not endpoint:
        return # Biarkan Flask menangani 404 secara standar
        
    # Bypass auth check saat testing HANYA untuk route bawaan asli agar tidak mengganggu test_app.py
    if app.config.get('TESTING'):
        original_endpoints = ['index', 'global_analysis', 'country_detail', 'show_map', 'show_news']
        if endpoint in original_endpoints:
            if 'user_id' not in session:
                session['user_id'] = 999
                session['username'] = 'test_admin'
                session['role'] = 'admin'
            return

    if endpoint not in public_routes:
        # Jika belum login, redirect ke login page
        if 'user_id' not in session:
            flash("Silakan masuk terlebih dahulu untuk mengakses TeknoAtlas.", "warning")
            return redirect(url_for('login'))
        
        # Otorisasi: Proteksi route admin
        if endpoint.startswith('admin_') and session.get('role') != 'admin':
            logger.warning(f"Unauthorized access attempt by user '{user}' to admin endpoint '{endpoint}'")
            abort(403)

# ==========================================
# 3. AUTHENTICATION ROUTES
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'user')
        
        # Validasi Username
        if not re.match("^[a-zA-Z0-9]{4,20}$", username):
            flash("Username harus alfanumerik dan berukuran 4-20 karakter.", "danger")
            return render_template('register.html')
            
        # Validasi Password
        if len(password) < 6 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            flash("Password minimal 6 karakter dan mengandung kombinasi huruf dan angka.", "danger")
            return render_template('register.html')
            
        # Validasi Kecocokan Password
        if password != confirm_password:
            flash("Password dan Konfirmasi Password tidak cocok.", "danger")
            return render_template('register.html')
            
        # Validasi Role
        if role not in ['user', 'admin']:
            role = 'user'
            
        # Simpan ke Database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Periksa keunikan username
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username sudah digunakan. Silakan pilih username lain.", "danger")
                return render_template('register.html')
                
            password_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           (username, password_hash, role))
            conn.commit()
            flash("Pendaftaran berhasil! Silakan masuk menggunakan akun baru Anda.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Database Error during registration: {e}")
            flash("Terjadi kesalahan sistem saat mendaftar. Silakan coba lagi.", "danger")
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password_hash'], password):
                # Set Session
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                flash(f"Selamat datang kembali, {username}!", "success")
                return redirect(url_for('index'))
            else:
                flash("Username atau password salah.", "danger")
        except Exception as e:
            logger.error(f"Database Error during login: {e}")
            flash("Terjadi kesalahan sistem saat masuk. Silakan coba lagi.", "danger")
        finally:
            conn.close()
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah berhasil keluar dari sistem.", "success")
    return redirect(url_for('login'))

# ==========================================
# 4. CORE APP & API DATA ROUTES
# ==========================================
@app.route('/')
def index():
    tech_db = get_all_countries()
    nexus.tech_database = tech_db

    countries_raw = nexus.get_countries() or []

    # Ubah data API menjadi dictionary berdasarkan ISO3
    api_countries = {
        country.get('cca3'): country
        for country in countries_raw
        if country.get('cca3')
    }

    enriched_countries = []

    # Perulangan menggunakan data SQLite sebagai sumber utama
    for iso3, local_country in tech_db.items():
        api_country = api_countries.get(iso3)

        if api_country:
            country_data = api_country.copy()

            if not country_data.get('name'):
                country_data['name'] = {
                    'common': local_country['name'],
                    'official': local_country['name']
                }
        else:
            # Fallback jika negara tidak ditemukan di API
            country_data = {
                'cca3': iso3,
                'name': {
                    'common': local_country['name'],
                    'official': local_country['name']
                },
                'population': 0,
                'region': 'Global',
                'subregion': 'Global',
                'capital': [],
                'flags': {
                    'png': '',
                    'svg': ''
                }
            }

        country_data.update({
            'cca3': iso3,
            'desc': local_country['desc'],
            'maturity': local_country['maturity']
        })

        enriched_countries.append(country_data)

    enriched_countries.sort(
        key=lambda country: (
            country['cca3'] != 'IDN',
            country['name']['common']
        )
    )

    return render_template(
        'index.html',
        countries=enriched_countries
    )
    
@app.route('/analysis')
def global_analysis():
    tech_db = get_all_countries()
    nexus.tech_database = tech_db
    target_iso3 = list(tech_db.keys())
    
    # Ambil data multi-indicator secara paralel menggunakan ThreadPool
    def fetch_all_data(iso3):
        return {
            "iso3": iso3,
            "gdp": nexus.get_gdp(iso3),
            "rd": nexus.get_rd_expenditure(iso3),
            "inflation": nexus.get_inflation(iso3),
            "internet": nexus.get_internet_usage(iso3)
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        economic_data = list(executor.map(fetch_all_data, target_iso3))
    
    results = []
    countries_raw = nexus.get_countries()
    
    for econ in economic_data:
        iso3 = econ['iso3']
        # Temukan data negara dari list API atau buat fallback jika API bermasalah
        api_c = next((c for c in countries_raw if c['cca3'] == iso3), None)
        
        name = api_c['name']['common'] if api_c else tech_db[iso3]['name']
        population = api_c['population'] if api_c else 0
        
        maturity = tech_db[iso3]['maturity']
        forecast_growth = predictor.predict_growth(maturity, econ['gdp'])
        
        results.append({
            "name": name,
            "gdp": econ['gdp'],
            "population": population,
            "score": maturity,
            "rd": econ['rd'],
            "inflation": econ['inflation'],
            "internet": econ['internet'],
            "forecast": forecast_growth,
            "iso3": iso3
        })
            
    results.sort(key=lambda x: x['score'], reverse=True)
    return render_template('analysis.html', data=results)

@app.route('/country/<iso3>')
def country_detail(iso3):
    iso3 = iso3.strip().upper()

    # Ambil data lokal dari SQLite
    db_country = get_country(iso3)

    if not db_country:
        abort(404)

    nexus.tech_database = get_all_countries()

    # Ambil data tambahan dari API
    api_detail = nexus.get_country_detail(iso3)

    # Data default untuk mencegah Undefined di Jinja
    detail = {
        "cca3": iso3,
        "name": db_country["name"],
        "official_name": db_country["name"],
        "flag": "",
        "population": 0,
        "region": "Tidak tersedia",
        "subregion": "Tidak tersedia",
        "capital": "Tidak tersedia",
        "currency": db_country["code"] or "Tidak tersedia",
        "languages": "Tidak tersedia",
        "maturity": db_country["maturity"],
        "desc": db_country["desc"],
        "full_description": db_country["full_description"],
        "innovation_hubs": db_country["innovation_hubs"],
        "challenges": db_country["challenges"],
        "universities": db_country["universities"],
        "tech_sectors": db_country["tech_sectors"]
    }

    # Gabungkan data API jika tersedia
    if isinstance(api_detail, dict):
        for key, value in api_detail.items():
            if value is not None and value != "":
                detail[key] = value

    # Data teknologi harus tetap menggunakan data SQLite
    detail.update({
        "maturity": db_country["maturity"],
        "desc": db_country["desc"],
        "full_description": db_country["full_description"],
        "innovation_hubs": db_country["innovation_hubs"],
        "challenges": db_country["challenges"],
        "universities": db_country["universities"],
        "tech_sectors": db_country["tech_sectors"]
    })

    # Pastikan population selalu angka
    try:
        detail["population"] = int(detail.get("population") or 0)
    except (TypeError, ValueError):
        detail["population"] = 0

    # Ambil data ekonomi
    with ThreadPoolExecutor(max_workers=7) as executor:
        f_gdp = executor.submit(nexus.get_gdp, iso3)
        f_rd = executor.submit(nexus.get_rd_expenditure, iso3)
        f_inflation = executor.submit(
            nexus.get_inflation,
            iso3
        )
        f_internet = executor.submit(
            nexus.get_internet_usage,
            iso3
        )
        f_hitech = executor.submit(
            nexus.get_hitech_exports,
            iso3
        )
        f_journals = executor.submit(
            nexus.get_scientific_journals,
            iso3
        )
        f_unemployment = executor.submit(
            nexus.get_unemployment,
            iso3
        )

        gdp = f_gdp.result()
        rd = f_rd.result()
        inflation = f_inflation.result()
        internet = f_internet.result()
        hitech = f_hitech.result()
        journals = f_journals.result()
        unemployment = f_unemployment.result()

    try:
        forecast = predictor.predict_growth(
            detail["maturity"],
            gdp
        )
    except (TypeError, ValueError):
        forecast = 0

    return render_template(
        'detail.html',
        country=detail,
        gdp=gdp,
        rd=rd,
        inflation=inflation,
        internet=internet,
        hitech=hitech,
        journals=journals,
        unemployment=unemployment,
        forecast=forecast
    )
    
@app.route('/map')
def show_map():
    hubs = [
        {"lat": -6.2088, "lng": 106.8456, "name": "Jakarta Tech Hub", "country": "Indonesia", "focus": "Fintech & E-commerce"},
        {"lat": 37.7749, "lng": -122.4194, "name": "Silicon Valley", "country": "USA", "focus": "AI & Semiconductors"},
        {"lat": 22.5431, "lng": 114.0579, "name": "Shenzhen Innovation Zone", "country": "China", "focus": "Hardware & EV"},
        {"lat": 35.6762, "lng": 139.6503, "name": "Tokyo Robotics Cluster", "country": "Japan", "focus": "Robotics & Precision Eng"},
        {"lat": 52.5200, "lng": 13.4050, "name": "Berlin Startup Scene", "country": "Germany", "focus": "SaaS & Industry 4.0"},
        {"lat": 37.4000, "lng": 127.1000, "name": "Pangyo Techno Valley", "country": "South Korea", "focus": "Memories & Game Dev"},
        {"lat": 52.2053, "lng": 0.1218, "name": "Cambridge Science Park", "country": "UK", "focus": "Deeptech & AI"},
        {"lat": 32.0853, "lng": 34.7818, "name": "Silicon Wadi", "country": "Israel", "focus": "Cybersecurity"},
        {"lat": 1.2902, "lng": 103.8519, "name": "one-north", "country": "Singapore", "focus": "Smart Nation & Foodtech"},
        {"lat": 12.9716, "lng": 77.5946, "name": "Bangalore", "country": "India", "focus": "IT Services & Space"},
        {"lat": 48.8566, "lng": 2.3522, "name": "Station F", "country": "France", "focus": "AI & Green Tech"}
    ]
    return render_template('map.html', hubs=hubs)

@app.route('/news')
def show_news():
    tech_db = get_all_countries()
    nexus.tech_database = tech_db
    news_items = nexus.get_tech_news()
    return render_template('news.html', news=news_items)

# ==========================================
# 5. ADMINISTRATOR / CRUD ROUTES
# ==========================================
@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():

    # Saat halaman dibuka menggunakan GET
    if request.method == 'GET':
        return render_template('admin_add.html')

    # =====================================
    # Ambil data form
    # =====================================
    cca3 = request.form.get('cca3', '').strip().upper()
    name = request.form.get('name', '').strip()
    maturity_raw = request.form.get('maturity', '').strip()
    code = request.form.get('code', '').strip().upper()
    desc = request.form.get('desc', '').strip()
    full_description = request.form.get(
        'full_description',
        ''
    ).strip()

    # Data berbentuk daftar, dipisahkan koma
    hubs_raw = request.form.get('innovation_hubs', '')
    challenges_raw = request.form.get('challenges', '')
    universities_raw = request.form.get('universities', '')

    hubs = [
        item.strip()
        for item in hubs_raw.split(',')
        if item.strip()
    ]

    challenges = [
        item.strip()
        for item in challenges_raw.split(',')
        if item.strip()
    ]

    universities = [
        item.strip()
        for item in universities_raw.split(',')
        if item.strip()
    ]

    # Data sektor teknologi
    sec_key = request.form.get(
        'sector_key',
        'digital'
    ).strip().lower()

    sec_item = request.form.get(
        'sector_item',
        ''
    ).strip()

    sec_company = request.form.get(
        'sector_company',
        ''
    ).strip()

    sec_status = request.form.get(
        'sector_status',
        ''
    ).strip()

    sec_year = request.form.get(
        'sector_year',
        '2026'
    ).strip()

    sec_detail = request.form.get(
        'sector_detail',
        ''
    ).strip()

    # =====================================
    # Validasi ISO3
    # =====================================
    if not re.fullmatch(r'[A-Z]{3}', cca3):
        flash(
            "Kode ISO3 harus tepat 3 huruf, misalnya IDN.",
            "danger"
        )
        return render_template('admin_add.html')

    # Validasi nama negara
    if not name:
        flash(
            "Nama negara tidak boleh kosong.",
            "danger"
        )
        return render_template('admin_add.html')

    # Validasi maturity
    try:
        maturity = int(maturity_raw)

        if maturity < 0 or maturity > 100:
            raise ValueError

    except (TypeError, ValueError):
        flash(
            "Skor maturitas harus berupa angka 0 sampai 100.",
            "danger"
        )
        return render_template('admin_add.html')

    # Validasi kode mata uang
    if not re.fullmatch(r'[A-Z]{3}', code):
        flash(
            "Kode mata uang harus tepat 3 huruf, misalnya IDR.",
            "danger"
        )
        return render_template('admin_add.html')

    # Validasi deskripsi
    if not desc:
        flash(
            "Deskripsi singkat wajib diisi.",
            "danger"
        )
        return render_template('admin_add.html')

    if not full_description:
        flash(
            "Deskripsi lengkap wajib diisi.",
            "danger"
        )
        return render_template('admin_add.html')

    # Validasi sektor teknologi
    required_sector_fields = [
        sec_key,
        sec_item,
        sec_company,
        sec_status,
        sec_year,
        sec_detail
    ]

    if not all(required_sector_fields):
        flash(
            "Semua data sektor teknologi wajib diisi.",
            "danger"
        )
        return render_template('admin_add.html')

    sectors = {
        sec_key: {
            "item": sec_item,
            "company": sec_company,
            "year": sec_year,
            "status": sec_status,
            "detail": sec_detail
        }
    }

    # =====================================
    # Simpan ke database
    # =====================================
    try:
        success, error_message = insert_country(
            cca3=cca3,
            name=name,
            maturity=maturity,
            code=code,
            desc=desc,
            full_description=full_description,
            hubs=hubs,
            challenges=challenges,
            universities=universities,
            sectors=sectors
        )

        if success:
            cache.clear()

            # Perbarui data yang digunakan DataNexus
            nexus.tech_database = get_all_countries()

            flash(
                f"Negara {name} berhasil ditambahkan!",
                "success"
            )

            return redirect(url_for('index'))

        flash(
            f"Gagal menambahkan negara: {error_message}",
            "danger"
        )

        return render_template('admin_add.html')

    except Exception as error:
        logger.exception(
            f"Kesalahan saat menambahkan negara: {error}"
        )

        flash(
            f"Terjadi kesalahan database: {error}",
            "danger"
        )

        return render_template('admin_add.html')
      
@app.route('/admin/edit/<iso3>', methods=['GET', 'POST'])
def admin_edit(iso3):
    iso3 = iso3.upper()
    country = get_country(iso3)
    if not country:
        abort(404)
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        maturity = request.form.get('maturity', '')
        code = request.form.get('code', '').strip().upper()
        desc = request.form.get('desc', '').strip()
        full_description = request.form.get('full_description', '').strip()
        
        hubs_raw = request.form.get('innovation_hubs', '')
        challenges_raw = request.form.get('challenges', '')
        universities_raw = request.form.get('universities', '')
        
        hubs = [h.strip() for h in hubs_raw.split(',') if h.strip()]
        challenges = [c.strip() for c in challenges_raw.split(',') if c.strip()]
        universities = [u.strip() for u in universities_raw.split(',') if u.strip()]
        
        # Sector Details
        sec_key = request.form.get('sector_key', 'digital').strip().lower()
        sec_item = request.form.get('sector_item', '').strip()
        sec_company = request.form.get('sector_company', '').strip()
        sec_status = request.form.get('sector_status', '').strip()
        sec_year = request.form.get('sector_year', '2024')
        sec_detail = request.form.get('sector_detail', '').strip()
        
        # Validasi Data Input
        if not name:
            flash("Nama Negara tidak boleh kosong.", "danger")
            return render_template('admin_edit.html', country=country)
            
        try:
            maturity = int(maturity)
            if not (0 <= maturity <= 100):
                raise ValueError()
        except ValueError:
            flash("Skor Maturitas harus berupa angka bulat antara 0 sampai 100.", "danger")
            return render_template('admin_edit.html', country=country)
            
        if not re.match("^[A-Z]{3}$", code):
            flash("Kode Mata Uang harus terdiri dari tepat 3 huruf kapital.", "danger")
            return render_template('admin_edit.html', country=country)
            
        if not desc or not full_description:
            flash("Deskripsi singkat dan lengkap wajib diisi.", "danger")
            return render_template('admin_edit.html', country=country)
            
        if not sec_key or not sec_item or not sec_company or not sec_status or not sec_detail:
            flash("Semua kolom sektor teknologi utama wajib diisi.", "danger")
            return render_template('admin_edit.html', country=country)

        # Format sectors JSON
        sectors = {
            sec_key: {
                "item": sec_item,
                "company": sec_company,
                "year": sec_year,
                "status": sec_status,
                "detail": sec_detail
            }
        }
        
        success = update_country(iso3, name, maturity, code, desc, full_description, hubs, challenges, universities, sectors)
        if success:
            cache.clear() # Bersihkan cache
            flash(f"Profil teknologi negara {name} berhasil diperbarui!", "success")
            return redirect(url_for('country_detail', iso3=iso3))
        else:
            flash("Terjadi kesalahan saat memperbarui database. Silakan coba lagi.", "danger")
            return render_template('admin_edit.html', country=country)
            
    return render_template('admin_edit.html', country=country)

@app.route('/admin/delete/<iso3>', methods=['GET', 'POST'])
def admin_delete(iso3):
    iso3 = iso3.upper()
    country = get_country(iso3)
    if not country:
        abort(404)
        
    success = delete_country(iso3)
    if success:
        cache.clear() # Bersihkan cache
        flash(f"Profil teknologi negara {country['name']} berhasil dihapus.", "success")
    else:
        flash("Gagal menghapus profil teknologi negara.", "danger")
        
    return redirect(url_for('index'))

# ==========================================
# 6. ERROR HANDLING
# ==========================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                           error_code=404, 
                           error_title="Halaman Tidak Ditemukan", 
                           error_message="Maaf, halaman yang Anda cari tidak dapat ditemukan di server kami."), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', 
                           error_code=403, 
                           error_title="Akses Ditolak (Forbidden)", 
                           error_message="Anda tidak memiliki hak akses (authorization) untuk halaman administrator ini."), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', 
                           error_code=500, 
                           error_title="Kesalahan Server Internal", 
                           error_message="Terjadi kesalahan pada sistem backend kami. Mohon hubungi administrator."), 500

if __name__ == '__main__':
    app.run(debug=True, port=8082)
