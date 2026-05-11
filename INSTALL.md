# Panduan Instalasi & Penggunaan - Kelompok 5

## Persyaratan Sistem
- Python 3.8 ke atas
- Koneksi Internet (untuk akses API Publik secara real-time)

## Langkah-langkah Instalasi

1. **Persiapan Virtual Environment (Opsional tapi Direkomendasikan)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/macOS
   # atau
   venv\Scripts\activate     # Untuk Windows
   ```

2. **Instalasi Library**
   Gunakan file `requirements.txt` yang sudah disediakan:
   ```bash
   pip install -r requirements.txt
   ```

3. **Menjalankan Server Flask**
   ```bash
   python app.py
   ```

## Struktur Proyek
- `app.py`: Server utama dan pengaturan rute (routing).
- `services.py`: Logika pengambilan data dari API Publik menggunakan library `requests`.
- `ml_engine.py`: Mesin analisis data (Machine Learning) sederhana.
- `templates/`: Kumpulan file HTML untuk tampilan website.
- `static/`: File CSS untuk desain tampilan.
- `data/`: Database internal tambahan dan model ML.

## Troubleshooting
- **API Timeout**: Jika data tidak muncul, pastikan koneksi internet stabil karena aplikasi melakukan request ke server internasional (World Bank & News Sites).
- **Module Not Found**: Pastikan sudah menjalankan `pip install` di dalam environment yang benar.
