Tentu, ini adalah draf `README.md` untuk proyek Anda yang dirancang khusus untuk menonjolkan penggunaan **PostgreSQL (Supabase)** dan **Redis (Upstash)** untuk *rate limiting* dan *caching*, sesuai dengan struktur proyek prediksi *churn* yang terlihat pada file Anda.

---

# 🔮 Churn Prediction API

Proyek ini adalah layanan *Machine Learning* *end-to-end* untuk memprediksi tingkat *churn* pelanggan. Dibangun dengan **Python** dan **CatBoost**, aplikasi ini dioptimalkan untuk performa tinggi dan skalabilitas menggunakan **Supabase** sebagai database utama dan **Upstash Redis** untuk manajemen trafik dan caching.

## 🚀 Teknologi Utama

Fokus utama arsitektur proyek ini adalah efisiensi data dan keamanan trafik API:

* **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
* **Rate Limiting & Caching:** [Upstash](https://upstash.com/) (Serverless Redis)
* **Machine Learning:** CatBoost
* **Data Versioning:** DVC (Data Version Control)
* **CI/CD:** GitHub Actions
* **Containerization:** Docker

---

## ⚡ Fitur Unggulan: Supabase & Upstash

### 1. Database & Penyimpanan (Supabase)

Kami menggunakan **Supabase** (PostgreSQL) sebagai solusi penyimpanan data yang *reliable* dan *scalable*.

* **Penyimpanan Data Historis:** Menyimpan data pelanggan mentah (`churn_data.csv`) dan data yang telah diproses untuk keperluan *retraining* model.
* **Log Prediksi:** Setiap permintaan prediksi yang masuk disimpan ke dalam tabel PostgreSQL untuk pemantauan performa model dan audit.
* **Autentikasi:** Mengelola akses pengguna ke API menggunakan fitur *Auth* bawaan Supabase.

### 2. Intelligent Caching (Upstash Redis) Untuk meminimalkan latensi dan beban komputasi pada model ML, kami mengimplementasikan strategi *caching* yang agresif menggunakan **Upstash Redis**:

* **Prediction Caching:** Hasil prediksi untuk input pelanggan yang sama disimpan di Redis dengan TTL (Time-to-Live) tertentu. Jika permintaan yang sama muncul kembali, API akan mengembalikan hasil dari *cache* secara instan tanpa menjalankan ulang model CatBoost.
* *Dampak:* Mengurangi waktu respons API hingga < 50ms untuk *request* berulang.



### 3. API Rate Limiting (Upstash Redis)

Untuk melindungi layanan dari penyalahgunaan (DDoS) dan memastikan ketersediaan bagi semua pengguna, kami menerapkan *Rate Limiting* berbasis Redis:

* **Sliding Window Algorithm:** Menggunakan Upstash untuk melacak jumlah permintaan per IP atau API Key secara *real-time*.
* **Batas:** Dikonfigurasi (contoh: 100 request/menit). Jika batas terlampaui, API akan secara otomatis mengembalikan respons `429 Too Many Requests`.

---

## 📂 Struktur Proyek

```bash
project-1/
├── .github/workflows/   # CI/CD Pipelines
├── catboost_info/       # Metadata & log training model CatBoost
├── data/                # Dikelola dengan DVC
│   ├── raw/             # Data mentah (churn_data.csv)
│   └── processed/       # Data siap latih
├── src/                 # Source code aplikasi (Python)
├── .dockerignore        # Konfigurasi Docker
└── README.md

```

## 🛠️ Cara Menjalankan

### Prasyarat

Pastikan Anda memiliki kredensial untuk Supabase dan Upstash.

1. Buat file `.env`:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
UPSTASH_REDIS_REST_URL=your_upstash_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_token

```



### Instalasi Lokal

```bash
# Clone repository
git clone https://github.com/username/project-1.git

# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
python main.py

```

### Menjalankan dengan Docker

```bash
docker build -t churn-prediction-api .
docker run -p 8000:8000 --env-file .env churn-prediction-api

```

## 🔄 CI/CD & Data Versioning

* **DVC:** Data latih (`data/`) dilacak menggunakan DVC untuk memastikan reprodukhibilitas eksperimen ML. Gunakan `dvc pull` untuk mengunduh data terbaru.
* **GitHub Actions:** Pipeline CI/CD (`.github/workflows/ci-cd.yml`) akan otomatis menjalankan tes dan men-deploy aplikasi ke server produksi setiap kali ada perubahan pada branch `main`.
