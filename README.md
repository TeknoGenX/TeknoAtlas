# TeknoAtlas: Global Innovation & Tech Insights (Kelompok 5)

## Informasi Kelompok
- **Kelas:** Pemrograman Back-End
- **Kelompok:** 5
- **Anggota:**
  1. [Nama Anggota 1]
  2. [Nama Anggota 2]
  3. [Nama Anggota 3]

## Tema Website
**TeknoAtlas** adalah platform dashboard analisis teknologi global yang mengintegrasikan data ekonomi makro dan warta teknologi internasional secara *real-time*. Aplikasi ini tidak hanya menampilkan data mentah, tetapi juga melakukan **Analisis Prediktif** menggunakan Machine Learning di sisi Back-End sebelum menyajikannya kepada pengguna.

## Integrasi API Publik
Sesuai dengan syarat tugas, aplikasi ini menggunakan library `requests` untuk mengambil data dari berbagai API publik:
1.  **RestCountries API**: Data dasar negara (Bendera, Populasi, Region).
2.  **World Bank API**: Data indikator ekonomi (GDP, pengeluaran R&D, tingkat inflasi, penggunaan internet).
3.  **Hacker News (Algolia) API**: Warta tren startup dan teknologi global.
4.  **Dev.to API**: Berita komunitas pengembang perangkat lunak internasional.
5.  **Spaceflight News API**: Informasi terkini mengenai teknologi antariksa.

## Fitur Utama & Analisis Back-End
1.  **Dashboard Dinamis**: Menampilkan profil teknologi berbagai negara yang dihasilkan dari penggabungan data API dan database internal.
2.  **Analisis Komparatif**: Tabel perbandingan ekonomi makro yang datanya dihitung dan diformat secara dinamis.
3.  **Machine Learning Forecasting**: Menggunakan `scikit-learn` untuk memprediksi potensi pertumbuhan ekonomi berdasarkan skor maturitas teknologi dan data GDP dari API.
4.  **Agregator Warta**: Menggabungkan berita dari 4 sumber internasional berbeda ke dalam satu tampilan terpadu.
5.  **Peta Inovasi**: Visualisasi lokasi pusat teknologi dunia menggunakan Leaflet.js.

## Syarat Teknis (Checklist Tugas)
- [x] **Framework**: Flask (Python)
- [x] **Library API**: `requests`
- [x] **Template Engine**: Jinja2 (HTML Template Flask) dengan Looping & Conditional.
- [x] **Tampilan**: Menggunakan Card, Table, dan Navigasi Sederhana (User Friendly).
- [x] **Data Dinamis**: Semua data diambil dari API dan diproses di server.

## Cara Menjalankan
1. Instalasi dependensi:
   ```bash
   pip install -r requirements.txt
   ```
2. Jalankan aplikasi:
   ```bash
   python app.py
   ```
3. Akses di browser: `http://127.0.0.1:5000`
