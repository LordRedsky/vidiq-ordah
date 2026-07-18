# 🎬 vidIQ Script Doctor & YouTube SEO Specialist

Aplikasi Streamlit berbasis **YouTube Data API v3** untuk melakukan riset tren video kompetitor, ekstraksi kata kunci SEO, serta audit retensi naskah narasi video YouTube.

## 🚀 Fitur Utama

- **📄 Audit Retensi Naskah (Script Doctor)**: Mengidentifikasi kalimat intro/outro bertele-tele, pembuka lambat, dan pengulangan basa-basi (*filler phrases*) agar *audience retention* tetap tinggi.
- **🎯 Riset Kata Kunci SEO**: Menarik kata kunci & tag secara *real-time* dari video kompetitor YouTube teratas.
- **📊 Metrik Retensi**: Menghitung skor SEO & retensi (0-100) serta memberikan rekomendasi kata kunci yang disarankan untuk disisipkan.
- **📥 Export Data**: Mengunduh hasil audit dalam format JSON.

## ⚙️ Cara Memulai

### 1. Clone Repository & Install Dependencies

```bash
git clone https://github.com/LordRedsky/vidiq-ordah.git
cd vidiq-ordah
pip install -r requirements.txt
```

### 2. Konfigurasi Environment Variable

Buat berkas `.env` di direktori utama project:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 3. Jalankan Aplikasi

```bash
streamlit run app.py
```
