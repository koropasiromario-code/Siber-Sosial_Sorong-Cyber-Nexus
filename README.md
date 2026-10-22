# Siber Sosial — Sorong Cyber Nexus

MVP aplikasi web untuk analisis percakapan publik dari CSV: sentimen sederhana, indikator konten sensasional, pola teks berulang, indikator aktivitas akun, visualisasi hubungan akun, peringatan lonjakan volume, dan ekspor hasil.

## Menjalankan aplikasi

Disarankan Python 3.10 atau lebih baru.

### Windows
1. Ekstrak ZIP.
2. Buka Command Prompt/PowerShell pada folder proyek.
3. Buat virtual environment:
   `py -m venv .venv`
4. Aktifkan:
   `.venv\\Scripts\\activate`
5. Instal dependensi:
   `pip install -r requirements.txt`
6. Jalankan:
   `streamlit run app.py`
7. Buka URL lokal yang ditampilkan, biasanya `http://localhost:8501`.

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Format CSV

Kolom wajib:
- `timestamp` — tanggal/waktu yang dapat dibaca pandas, misalnya `2026-10-22 08:30:00`
- `platform` — nama platform/sumber
- `account` — nama akun atau ID pseudonim
- `text` — isi teks yang dianalisis

Kolom opsional:
- `likes`, `shares`, `replies` — angka
- `reply_to` — akun yang dibalas, jika tersedia

Unduh template CSV langsung dari tab **Data & Ekspor**. Dataset demo otomatis tersedia untuk mencoba dashboard.

## Apa yang dilakukan MVP
- Sentimen: leksikon kecil Bahasa Indonesia; bukan model NLP yang dilatih.
- Indikasi disinformasi: frasa sensasional, tanda baca, dan pola bahasa; bukan pemeriksaan fakta.
- Indikasi bot/koordinasi: volume unggahan per akun dan teks berulang.
- Jaringan: hubungan `reply_to` dan kesamaan teks yang persis.
- Peringatan dini: volume per 15 menit dibanding ambang heuristik.
- Ekspor: CSV hasil analisis dan template input.

## Batasan dan penggunaan yang bertanggung jawab
- Tidak mengambil data langsung dari platform; impor hanya data yang Anda berwenang proses.
- Tidak menyatakan klaim sebagai hoaks secara otomatis dan tidak memvonis akun sebagai bot/buzzer.
- Skor hanya membantu menentukan prioritas peninjauan manusia. Bahasa satir, kutipan, konteks lokal, dan dialek dapat menghasilkan kesalahan.
- Jangan gunakan skor ini sebagai satu-satunya dasar untuk menuduh, menghukum, memprofilkan, atau mengambil tindakan terhadap individu.
- Untuk produksi: tambahkan autentikasi, kontrol akses, audit log, enkripsi, kebijakan retensi data, validasi sumber, model Bahasa Indonesia yang tervalidasi, dan integrasi platform resmi sesuai ketentuan layanan serta hukum yang berlaku.

## Identitas
**Tim pengembang: Sorong Cyber Nexus**
