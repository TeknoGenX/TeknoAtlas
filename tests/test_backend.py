import pytest
import os
import re
import json
import database
from app import app as flask_app
from werkzeug.security import generate_password_hash

# Fixture untuk menggunakan database testing terpisah
@pytest.fixture(autouse=True)
def setup_test_db():
    original_path = database.DATABASE_PATH
    database.DATABASE_PATH = 'data/test_teknoatlas.db'
    database.init_db()
    yield
    # Hapus database testing setelah pengujian selesai
    if os.path.exists('data/test_teknoatlas.db'):
        try:
            os.remove('data/test_teknoatlas.db')
        except OSError:
            pass
    database.DATABASE_PATH = original_path

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-key-123"
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

# ==========================================
# 1. UNIT TESTS: DATABASE & HELPERS
# ==========================================
class TestDatabaseHelpers:
    def test_init_db_seeds_default_users(self):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        users = {row['username']: row['role'] for row in cursor.fetchall()}
        conn.close()
        
        assert 'admin' in users
        assert users['admin'] == 'admin'
        assert 'user' in users
        assert users['user'] == 'user'

    def test_crud_helpers(self):
        # Insert Country
        success = database.insert_country(
            cca3="XYZ", name="Testland", maturity=92, code="XYZ",
            desc="Hub teknologi pintar.", full_description="Singapura adalah negara maju...",
            hubs=["one-north", "Block 71"], challenges=["Talenta", "Lahan"],
            universities=["NUS", "NTU"],
            sectors={"digital": {"item": "Smart Nation", "company": "GovTech", "year": "2024", "status": "Active", "detail": "Detail"}}
        )
        assert success is True
        
        # Get Country
        country = database.get_country("XYZ")
        assert country is not None
        assert country['name'] == "Testland"
        assert country['maturity'] == 92
        assert "one-north" in country['innovation_hubs']
        
        # Update Country
        update_success = database.update_country(
            cca3="XYZ", name="Testland Updated", maturity=95, code="XYZ",
            desc="Hub teknologi pintar.", full_description="Singapura adalah negara maju...",
            hubs=["one-north", "Block 71"], challenges=["Talenta"],
            universities=["NUS"], sectors={}
        )
        assert update_success is True
        
        country = database.get_country("XYZ")
        assert country['name'] == "Testland Updated"
        assert country['maturity'] == 95
        
        # Delete Country
        delete_success = database.delete_country("XYZ")
        assert delete_success is True
        assert database.get_country("XYZ") is None

# ==========================================
# 2. INTEGRATION TESTS: AUTHENTICATION
# ==========================================
class TestAuthenticationFlows:
    def test_register_validation_invalid_username(self, client):
        # Username terlalu pendek (3 karakter)
        response = client.post('/register', data={
            'username': 'abc',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'user'
        })
        assert b"Username harus alfanumerik" in response.data

    def test_register_validation_invalid_password(self, client):
        # Password tidak ada angka
        response = client.post('/register', data={
            'username': 'validuser',
            'password': 'password',
            'confirm_password': 'password',
            'role': 'user'
        })
        assert b"Password minimal 6 karakter" in response.data

    def test_register_validation_mismatched_password(self, client):
        response = client.post('/register', data={
            'username': 'validuser',
            'password': 'password123',
            'confirm_password': 'different123',
            'role': 'user'
        })
        assert b"Password dan Konfirmasi Password tidak cocok" in response.data

    def test_register_success(self, client):
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'role': 'user'
        }, follow_redirects=True)
        assert b"Pendaftaran berhasil" in response.data
        
        # Cek apakah user ada di DB
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ('newuser',))
        user = cursor.fetchone()
        conn.close()
        assert user is not None
        assert user['role'] == 'user'

    def test_login_failed(self, client):
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        assert b"Username atau password salah" in response.data

    def test_login_success(self, client):
        response = client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        }, follow_redirects=True)
        assert b"Selamat datang kembali" in response.data
        
        with client.session_transaction() as sess:
            assert sess.get('username') == 'user'
            assert sess.get('role') == 'user'

    def test_logout(self, client):
        # Login dulu
        client.post('/login', data={'username': 'user', 'password': 'user123'})
        response = client.get('/logout', follow_redirects=True)
        assert b"Anda telah berhasil keluar" in response.data
        
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

# ==========================================
# 3. INTEGRATION TESTS: AUTHORIZATION & CRUD
# ==========================================
class TestAuthorizationAndCRUD:
    def test_guest_redirect_to_login(self, client):
        # Matikan bypass TESTING mode secara manual untuk mengetes Middleware Auth asli
        flask_app.config["TESTING"] = False
        try:
            response = client.get('/', follow_redirects=True)
            assert b"Silakan masuk terlebih dahulu" in response.data
            assert b"Selamat Datang" in response.data # Mengarah ke Login Page
        finally:
            flask_app.config["TESTING"] = True

    def test_normal_user_cannot_access_admin_routes(self, client):
        # Login sebagai normal user
        client.post('/login', data={'username': 'user', 'password': 'user123'})
        
        # Matikan bypass TESTING mode agar Middleware mendeteksi session sesungguhnya
        flask_app.config["TESTING"] = False
        try:
            # Akses halaman Tambah Negara
            response = client.get('/admin/add')
            assert response.status_code == 403
            
            # Coba post Tambah Negara
            response = client.post('/admin/add', data={
                'cca3': 'SGP', 'name': 'Singapore', 'maturity': '80'
            })
            assert response.status_code == 403
        finally:
            flask_app.config["TESTING"] = True

    def test_admin_can_access_admin_routes_and_crud(self, client):
        # Login sebagai admin
        client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        
        flask_app.config["TESTING"] = False
        try:
            # Akses halaman Tambah
            response = client.get('/admin/add')
            assert response.status_code == 200
            assert b"Tambah Profil Teknologi Negara" in response.data
            
            # Post tambah negara baru (CRUD: Create)
            response = client.post('/admin/add', data={
                'cca3': 'MYS',
                'name': 'Malaysia',
                'maturity': '72',
                'code': 'MYR',
                'desc': 'Fokus manufaktur semikonduktor hulu.',
                'full_description': 'Malaysia memposisikan diri sebagai pusat pengemasan chip global.',
                'innovation_hubs': 'Penang Silicon Island, Cyberjaya',
                'challenges': 'Keterbatasan talenta IC design',
                'universities': 'Universitas Malaya, USM',
                'sector_key': 'semiconductor',
                'sector_item': 'Backend Assembly & Test',
                'sector_company': 'Intel Malaysia, ASE',
                'sector_status': 'Mature',
                'sector_year': '2023',
                'sector_detail': 'Pengembangan kapasitas pengemasan chip 3D tingkat lanjut.'
            }, follow_redirects=True)
            
            assert b"Profil teknologi untuk negara Malaysia berhasil ditambahkan" in response.data
            
            # Cek di database (CRUD: Read)
            country = database.get_country("MYS")
            assert country is not None
            assert country['name'] == 'Malaysia'
            assert country['maturity'] == 72
            assert 'Penang Silicon Island' in country['innovation_hubs']
            
            # Coba edit negara tersebut (CRUD: Update)
            response = client.post('/admin/edit/MYS', data={
                'name': 'Malaysia Baru',
                'maturity': '80',
                'code': 'MYR',
                'desc': 'Deskripsi baru.',
                'full_description': 'Latar belakang baru.',
                'innovation_hubs': 'Cyberjaya Baru',
                'challenges': 'Tantangan baru',
                'universities': 'Universitas Baru',
                'sector_key': 'digital',
                'sector_item': 'Sektor Baru',
                'sector_company': 'Perusahaan Baru',
                'sector_status': 'Active',
                'sector_year': '2024',
                'sector_detail': 'Detail Baru'
            }, follow_redirects=True)
            
            assert b"Profil teknologi negara Malaysia Baru berhasil diperbarui" in response.data
            
            country = database.get_country("MYS")
            assert country['name'] == 'Malaysia Baru'
            assert country['maturity'] == 80
            
            # Hapus negara tersebut (CRUD: Delete)
            response = client.get('/admin/delete/MYS', follow_redirects=True)
            assert b"Profil teknologi negara Malaysia Baru berhasil dihapus" in response.data
            assert database.get_country("MYS") is None
        finally:
            flask_app.config["TESTING"] = True
