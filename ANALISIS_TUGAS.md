# Analisis Kesesuaian Tugas - Kelompok 5

Dokumen ini menjelaskan bagaimana proyek **TeknoAtlas** memenuhi kriteria **Tugas 1 Kelompok** mata kuliah Pemrograman Back-End.

### 1. Struktur Halaman & Navigasi
- **Status**: [LULUS]
- **Penjelasan**: Website memiliki arsitektur multi-halaman yang rapi:
    - **Halaman Beranda**: Menampilkan data negara dalam bentuk **Card** dinamis.
    - **Halaman Peta**: Menampilkan **Peta Interaktif** hub inovasi.
    - **Halaman Warta**: Menampilkan **Daftar Berita** (List) dari API internasional.
    - **Halaman Analisis**: Menampilkan **Tabel Analisis** ekonomi makro.
- **Navigasi**: Menggunakan Navbar yang konsisten di bagian atas setiap halaman untuk memudahkan pengguna berpindah fitur.

### 2. Pengambilan Data API (Library `requests`)
- **Status**: [LULUS]
- **Penjelasan**: Seluruh pengambilan data dilakukan di `services.py` menggunakan library `requests`. Contoh penggunaan: `requests.get(url, timeout=10)`.

### 3. Menampilkan Data Dinamis
- **Status**: [LULUS]
- **Penjelasan**: 
    - Menggunakan **Looping** (`{% for ... %}`) di file `index.html`, `analysis.html`, dan `news.html`.
    - Menggunakan **Conditional** (`{% if ... %}`) untuk menangani error data.
    - Data ditampilkan dalam bentuk **Card** (Beranda & Berita) dan **Table** (Analisis).

### 4. Tampilan User Friendly
- **Status**: [LULUS]
- **Penjelasan**: Desain menggunakan CSS modern (Plus Jakarta Sans font, CSS Variables, Flexbox/Grid) untuk memastikan tampilan profesional, responsif, dan mudah dibaca (Judul jelas, gambar bendera, deskripsi terformat).

### 5. Analisis Back-End (Nilai Tambah)
- Proyek ini melampaui standar minimal dengan menambahkan:
    - **Machine Learning**: Prediksi pertumbuhan ekonomi.
    - **Caching**: Mengurangi beban API dan mempercepat loading.
    - **Multi-Source News**: Menggabungkan 4 API berita berbeda.
