# Laporan Tugas 2 Kelompok: Pemrograman Back-End
**Mata Kuliah:** Pemrograman Back-End  
**Dosen Pengampu:** Anas Nasrulloh, S.Kom., M.Kom.  
**Kelompok:** Kelompok 5  
**Judul Proyek:** TeknoAtlas - Eksplorasi Ekosistem Inovasi Dunia  

---

## 👥 Anggota Kelompok
1. **[Nama Mahasiswa 1]** - NIM: `[NIM Mahasiswa 1]`
2. **[Nama Mahasiswa 2]** - NIM: `[NIM Mahasiswa 2]`
3. **[Nama Mahasiswa 3]** - NIM: `[NIM Mahasiswa 3]`

---

## 📌 1. Latar Belakang Singkat
**TeknoAtlas** adalah platform analisis strategis berbasis web yang dirancang untuk memetakan, menganalisis, dan membandingkan ekosistem teknologi nasional di berbagai belahan dunia. 

Di era digital dan geopolitik teknologi yang bergerak cepat, pemangku kebijakan, pelaku industri, akademisi, dan mahasiswa memerlukan data komparatif yang valid untuk melihat sejauh mana kesiapan teknologi (*tech maturity*) suatu negara. TeknoAtlas menggabungkan data internal (deskripsi kualitatif profil teknologi, daftar universitas utama, hub inovasi, tantangan nasional) dengan data ekonomi makro yang diambil secara *real-time* dari API Publik (RestCountries dan World Bank). 

Platform ini juga dilengkapi dengan integrasi Machine Learning (ML) sederhana menggunakan Regresi Linier untuk memproyeksikan potensi pertumbuhan ekonomi berdasarkan tingkat maturitas teknologi negara.

---

## 🛠️ 2. Teknologi yang Digunakan
Aplikasi dibangun menggunakan *stack* teknologi yang modern, modular, dan ringan:
1. **Python 3.8+**: Bahasa pemrograman utama untuk logika back-end.
2. **Flask**: Microframework Python untuk routing, manajemen session, dan penanganan HTTP request.
3. **SQLite**: Sistem Manajemen Database (DBMS) relasional yang ringan untuk menyimpan data pengguna dan profil teknologi negara.
4. **HTML5, Vanilla CSS3 (Custom Variables), & JavaScript**: Sisi front-end untuk menyajikan antarmuka pengguna yang responsif, modern, dan interaktif.
5. **Leaflet.js**: Library JavaScript untuk rendering peta interaktif titik koordinat hub inovasi.
6. **Scikit-Learn & Joblib**: Library Python untuk operasionalisasi model prediksi Machine Learning (ML) Regresi Linier.
7. **Flask-Caching**: Untuk optimasi performa melalui mekanisme caching data API eksternal yang lambat.
8. **Requests**: Library Python untuk fetch data dari API Publik.

---

## 🌐 3. API Publik yang Digunakan
Website menggunakan dua API Publik utama yang dihubungi menggunakan library `requests` di Python:
1. **RestCountries API** (`https://www.apicountries.com/countries` dan `https://www.apicountries.com/alpha/{iso3}`): Digunakan untuk mengambil informasi profil geografis negara seperti nama resmi, wilayah, populasi, ibu kota, mata uang, dan bendera secara dinamis.
2. **World Bank Open Data API** (`https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}`): Digunakan untuk mengambil indikator ekonomi makro *real-time* dengan parameter *Most Recent Value* (MRV) untuk:
   - **GDP Current USD** (`NY.GDP.MKTP.CD`)
   - **R&D Expenditure (% of GDP)** (`GB.XPD.RSDV.GD.ZS`)
   - **Inflation Rate** (`FP.CPI.TOTL.ZG`)
   - **Internet Usage (% of Population)** (`IT.NET.USER.ZS`)
   - **High-technology exports (% of manufactured exports)** (`TX.VAL.TECH.ZS.DG`)
   - **Scientific and technical journal articles** (`IP.JRN.ARTC.SC`)
   - **Unemployment, total (% of total labor force)** (`SL.UEM.TOTL.ZS`)
3. **Public News APIs**: Dev.to API, Hacker News API, dan saurav.tech NewsAPI mirror untuk menyajikan warta berita teknologi dunia.

---

## 🗄️ 4. Struktur Database (SQLite)
Database SQLite disimpan pada file `data/teknoatlas.db`. Database ini terdiri dari 2 tabel utama yang terhubung secara relasional:

### A. Tabel `users`
Digunakan untuk menyimpan kredensial pengguna guna mendukung fitur Authentication & Authorization.
| Kolom | Tipe Data | Atribut | Keterangan |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identifier unik untuk setiap user. |
| `username` | TEXT | UNIQUE, NOT NULL | Nama pengguna untuk login. |
| `password_hash` | TEXT | NOT NULL | Hash password yang dienkripsi menggunakan Werkzeug. |
| `role` | TEXT | DEFAULT 'user' | Peran pengguna (`user` atau `admin`). |

### B. Tabel `countries`
Digunakan untuk menyimpan profil teknologi internal negara untuk memfasilitasi operasi CRUD.
| Kolom | Tipe Data | Keterangan |
|---|---|---|
| `cca3` | TEXT (3) | **PRIMARY KEY**. Kode ISO3 negara (Contoh: `IDN`, `USA`). |
| `name` | TEXT | Nama umum negara (Contoh: `Indonesia`). |
| `maturity` | INTEGER | Skor maturitas teknologi nasional (skala 0-100). |
| `code` | TEXT | Kode mata uang (Contoh: `IDR`). |
| `desc` | TEXT | Deskripsi singkat negara yang ditampilkan di halaman beranda. |
| `full_description`| TEXT | Deskripsi mendalam sejarah dan transformasi teknologi negara. |
| `innovation_hubs` | TEXT (JSON) | Array berisi daftar nama hub inovasi utama (di-serialize menjadi JSON). |
| `challenges` | TEXT (JSON) | Array berisi tantangan inovasi nasional. |
| `universities` | TEXT (JSON) | Array berisi universitas STEM utama di negara tersebut. |
| `tech_sectors` | TEXT (JSON) | Objek JSON terstruktur yang berisi data sektor teknologi strategis. |

---

## 🚦 5. Daftar Endpoint API (Flask Routing)
Berikut adalah daftar endpoint HTTP yang diimplementasikan pada aplikasi Flask:

| Method | Endpoint | Fungsi | Hak Akses |
|---|---|---|---|
| **GET** | `/register` | Menampilkan halaman pendaftaran akun baru. | Publik |
| **POST** | `/register` | Memproses pendaftaran akun baru dengan validasi. | Publik |
| **GET** | `/login` | Menampilkan halaman masuk akun. | Publik |
| **POST** | `/login` | Memproses verifikasi masuk akun. | Publik |
| **GET** | `/logout` | Menghapus session pengguna dan keluar. | Logged-in |
| **GET** | `/` | Dashboard utama / Beranda menampilkan kartu negara. | Logged-in (User & Admin) |
| **GET** | `/analysis` | Menampilkan tabel analisis komparatif indikator API & ML. | Logged-in (User & Admin) |
| **GET** | `/country/<iso3>` | Menampilkan profil teknologi mendalam per negara. | Logged-in (User & Admin) |
| **GET** | `/map` | Menampilkan peta interaktif hub inovasi dunia. | Logged-in (User & Admin) |
| **GET** | `/news` | Menampilkan warta berita teknologi dunia. | Logged-in (User & Admin) |
| **GET** | `/admin/add` | Menampilkan form tambah negara baru. | Admin |
| **POST** | `/admin/add` | Memproses pembuatan negara baru ke database (CRUD C). | Admin |
| **GET** | `/admin/edit/<iso3>`| Menampilkan form ubah data negara yang ada. | Admin |
| **POST**| `/admin/edit/<iso3>`| Memproses pembaruan data negara di database (CRUD U). | Admin |
| **GET** | `/admin/delete/<iso3>`| Memproses penghapusan data negara (CRUD D). | Admin |

---

## ⚙️ 6. Penjelasan Fitur Back-End

### A. Authentication
Fitur autentikasi bertugas memverifikasi identitas pengguna yang mengakses aplikasi:
- **Pendaftaran (Register):** Memungkinkan pengunjung membuat akun baru dengan menentukan username, password, dan *role* (User biasa atau Admin). Password tidak disimpan langsung, melainkan di-hash menggunakan algoritma enkripsi aman `pbkdf2:sha256` lewat fungsi `generate_password_hash()` dari modul `werkzeug.security`.
- **Masuk (Login):** Pengguna memasukkan username dan password. Back-end mencocokkan hash password yang tersimpan di database dengan password input menggunakan fungsi `check_password_hash()`. Jika cocok, data user dimasukkan ke dalam `session` Flask (terenkripsi dengan `app.secret_key`).
- **Keluar (Logout):** Sesi pengguna dihapus seluruhnya (`session.clear()`), sehingga hak akses dibatalkan dan diarahkan kembali ke halaman login.

### B. Authorization
Otorisasi membatasi tindakan yang dapat dilakukan oleh pengguna berdasarkan peran (*role*) yang dimilikinya setelah sukses terautentikasi:
- **Guest (Belum Login):** Hanya diperbolehkan mengakses halaman `/login`, `/register`, dan file statis (CSS/JS). Upaya mengakses halaman lain akan dialihkan kembali ke login.
- **Pengguna Biasa (role='user'):** Dapat melihat semua visualisasi data (Beranda/Dashboard, Detail Negara, Analisis Komparatif, Peta Hub, Berita). Namun, mereka **tidak memiliki tombol manajemen** dan **tidak diperbolehkan** mengakses rute administratif CRUD. Jika memaksa mengakses rute admin secara manual via URL, sistem secara otomatis menggagalkan dengan status **403 Forbidden**.
- **Administrator (role='admin'):** Memiliki otorisasi penuh untuk melihat dashboard dan melakukan tindakan CRUD (menambah negara baru, mengubah profil teknologi, dan menghapus negara) melalui antarmuka khusus.

### C. Validation (Validasi Form)
Sebelum data diproses oleh database, back-end melakukan pemeriksaan ketat untuk menjamin integritas data:
- **Registrasi Akun:**
  - Username wajib berupa alfanumerik (huruf/angka tanpa spasi) dengan panjang 4 s.d. 20 karakter (diuji menggunakan Regex: `^[a-zA-Z0-9]{4,20}$`).
  - Password wajib minimal 6 karakter dan mengandung sekurang-kurangnya 1 huruf dan 1 angka.
  - Password dan konfirmasi password harus cocok secara string.
  - Username harus unik (dilakukan pemeriksaan select query terlebih dahulu sebelum insert).
- **Penambahan & Pembaruan Negara (CRUD):**
  - Kode ISO3 Negara (`cca3`) wajib tepat 3 huruf kapital (Regex: `^[A-Z]{3}$`).
  - Kode Mata Uang (`code`) wajib tepat 3 huruf kapital (Regex: `^[A-Z]{3}$`).
  - Skor Maturitas Teknologi wajib berupa angka bulat di rentang 0 s.d. 100.
  - Deskripsi singkat, deskripsi lengkap, serta field sektor teknologi wajib terisi dan tidak boleh hanya berisi whitespace.

### D. Error Handling
Aplikasi memiliki penanganan kesalahan terpusat untuk menampilkan pesan yang ramah pengguna alih-alih error raw crash dari server:
- **404 Not Found:** Ditrigger jika rute tidak terdaftar atau ID negara yang dicari di URL `/country/<iso3>` tidak ada dalam database. Menampilkan halaman `error.html` berdesain premium dengan kode 404.
- **403 Forbidden:** Ditrigger jika pengguna non-admin mencoba memaksa masuk ke endpoint admin `/admin/*`. Menampilkan pesan penolakan otoritas dengan tombol redirect cepat untuk masuk akun yang sesuai.
- **500 Internal Server Error:** Ditrigger jika terjadi error tak terduga pada server database atau parser API. Menampilkan permintaan maaf ramah pengguna dan menyarankan untuk menghubungi administrator.

### E. Middleware
Diimplementasikan menggunakan hook `@app.before_request` Flask yang bertindak sebagai *interceptor* di tingkat global aplikasi:
1. **Request Logging:** Middleware mencatat setiap request HTTP yang masuk (Metode, Endpoint, IP, Username, dan Role) ke dalam logs konsol server guna keperluan audit dan debugging.
2. **Access Control List (ACL):** Middleware menyeleksi rute mana saja yang boleh dilewati oleh guest (rute login/register/static). Jika rute privat dicoba diakses tanpa sesi aktif, middleware langsung memotong siklus request dan me-redirect ke login dengan pesan peringatan.
3. **Role Enforcement:** Middleware memeriksa apakah endpoint yang dicari diawali dengan prefiks `/admin/` (nama fungsi handler `admin_`). Jika ya, dan session role bukan `admin`, middleware akan melempar error HTTP 403 sebelum routing mencapai controller utama.

---

## 🏃 7. Cara Menjalankan Aplikasi
1. **Siapkan Virtual Environment (venv):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Instalasi Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan Aplikasi:**
   ```bash
   python app.py
   ```
4. **Buka Aplikasi di Browser:**
   Akses alamat `http://127.0.0.1:8082/`.

*Catatan: Database SQLite (`data/teknoatlas.db`) akan secara otomatis terbuat dan diisi data seed (termasuk user demo `admin`/`admin123` dan `user`/`user123`) saat aplikasi dijalankan pertama kali.*

---

## 👥 8. Pembagian Tugas Anggota Kelompok
- **[Nama Mahasiswa 1]:**
  - Mendesain layout visual antarmuka website menggunakan Vanilla CSS (variabel warna, grid, flexbox, animasi micro-interaction).
  - Membuat template halaman login, register, dan dashboard beranda.
  - Integrasi Leaflet.js untuk peta hub inovasi dan styling popup peta.
- **[Nama Mahasiswa 2]:**
  - Mengembangkan modul database SQLite (`database.py`), mendesain skema tabel `users` dan `countries`, serta menulis helper CRUD.
  - Integrasi API Publik RestCountries dan World Bank menggunakan library `requests` di `services.py`.
  - Membuat rute kontroler CRUD admin (`/admin/add`, `/admin/edit`, `/admin/delete`) dan logic validasi form input back-end.
- **[Nama Mahasiswa 3]:**
  - Mengimplementasikan alur autentikasi (login, register, logout) dan hashing password.
  - Menulis middleware akses global (`@app.before_request`) untuk otorisasi hak akses user dan admin.
  - Mengembangkan sistem penanganan error terpusat (`@app.errorhandler`) untuk 404, 403, dan 500.
  - Membuat pengujian unit dan integrasi otomatis (`tests/`) menggunakan framework PyTest.
