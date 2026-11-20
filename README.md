<div align="center">
  <h1>📊 NestJS ORM Benchmark — Analysis</h1>

  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
    <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" />
    <img src="https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white" />
    <img src="https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=plotly&logoColor=white" />
  </p>

  <p>
    <strong>Analisis statistik hasil benchmark Prisma, TypeORM, Drizzle ORM, dan Raw SQL pada NestJS</strong><br />
  </p>
</div>

---

## 🌟 Overview

> Repository ini berisi **data hasil pengujian dan seluruh script analisisnya**: statistik deskriptif, uji inferensial (Friedman + Wilcoxon post-hoc), visualisasi, serta analisis penggunaan resource (CPU & RAM) dari pengujian diagnostik yang terpisah.

Aplikasi NestJS dan skrip pengujian beban (k6) berada di repository terpisah: [`nestjs-orm-benchmark`](https://github.com/WahyuPratama222/nestjs-orm-benchmark). Repository ini hanya memuat tahap **olah data**, sehingga semua angka di artikel bisa direproduksi dari dua file CSV input. Analisis ini mendukung artikel *Analisis Komparatif Performa Prisma, TypeORM, Drizzle, dan Raw SQL pada REST API berbasis NestJS dalam Berbagai Tingkat Konkurensi*.

### Lingkup pengujian

| Aspek | Nilai |
|-------|-------|
| Pendekatan akses data | Prisma, TypeORM, Drizzle ORM, Raw SQL |
| Operasi | `read`, `create`, `join`, `groupby` |
| Beban (VU) | 10, 50, 100 |
| Pengulangan | 10 per skenario |
| Metrik performa | P95 latency (`p95_ms`) dan throughput (`throughput_rps`) |
### Dua dataset yang terpisah

Analisis memakai dua dataset dari pengujian yang berbeda, dan keduanya **tidak digabung**:

| | Dataset performa | Dataset resource (diagnostik) |
|---|---|---|
| Tujuan | Membandingkan P95 latency dan throughput | Mengamati CPU dan RAM saat throughput stagnan |
| Cakupan | 4 ORM × 4 operasi × 3 VU × 10 pengulangan | 4 ORM × operasi `groupby` × 50 dan 100 VU × 3 pengulangan |
| Jumlah sampel | 480 | 24 |
| Alat ukur | k6 | `docker stats` (container API dan PostgreSQL) |
| Analisis | Deskriptif, inferensial, visualisasi | Deskriptif saja |

### Alur analisis

```
data/performance/performance_results.csv ──► statistik deskriptif ──► tabel
                                         ──► uji Friedman ──► Wilcoxon post-hoc ──► ringkasan
                                         ──► visualisasi (line & boxplot)

data/resource/resource_results.csv       ──► ringkasan CPU & RAM per sampel dan per ORM
                                             (dataset diagnostik terpisah)
```

---

## 📋 Daftar Isi

1. [Struktur Folder](#-1-struktur-folder)
2. [Fungsi Setiap File](#-2-fungsi-setiap-file)
3. [Setup](#️-3-setup)
4. [Menjalankan Analisis](#-4-menjalankan-analisis)
5. [Metode Statistik](#-5-metode-statistik)
6. [Verifikasi Hasil (`checks/`)](#-6-verifikasi-hasil-checks)

---

## 📁 1. Struktur Folder

```
nestjs-orm-benchmark-analysis/
├── data/                                  # INPUT (tidak diubah oleh script)
│   ├── performance/
│   │   └── performance_results.csv
│   └── resource/
│       └── resource_results.csv
├── scripts/
│   ├── performance/                       # Pipeline analisis performa
│   │   ├── compute_descriptive_stats.py
│   │   ├── generate_descriptive_table.py
│   │   ├── run_statistical_analysis.py
│   │   ├── summarize_statistical_results.py
│   │   ├── visualize_p95_line.py
│   │   ├── visualize_p95_boxplot.py
│   │   ├── visualize_throughput_line.py
│   │   └── visualize_throughput_boxplot.py
│   ├── resource/                          # Pipeline analisis resource
│   │   └── analyze_resource.py
│   └── checks/                            # Verifikasi manual (bukan bagian pipeline)
│       ├── check_friedman.py
│       ├── check_wilcoxon.py
│       ├── check_rbc.py
│       └── plot_raw_groupby_100vu.py
├── outputs/                               # OUTPUT (dihasilkan ulang oleh script)
│   ├── performance/
│   │   ├── descriptive/                   # Statistik deskriptif & tabel
│   │   ├── inferential/                   # Hasil Friedman, Wilcoxon, ringkasan
│   │   └── figures/                       # Grafik (PNG)
│   └── resource/                          # Ringkasan CPU & RAM
├── config.py                              # Semua path input/output di satu tempat
├── requirements.txt
└── README.md
```

> **Aturan sederhana:** `data/` adalah input, `outputs/` adalah hasil. Semua isi `outputs/` bisa dihapus lalu dibuat ulang dengan menjalankan script.

---

## 🧩 2. Fungsi Setiap File

### 📥 Data (input)

| File | Isi |
|------|-----|
| `data/performance/performance_results.csv` | Hasil tiap pengulangan: `repetition`, `orm`, `operation`, `vus`, `valid`, `p95_ms`, `throughput_rps`. Hanya baris dengan `valid = 1` yang dianalisis. |
| `data/resource/resource_results.csv` | Hasil `docker stats` dari pengujian diagnostik yang terpisah dari 480 sampel utama (24 sampel: `groupby`, 50 dan 100 VU, 3 pengulangan): `sample`, `timestamp`, `container`, `cpu_percent`, `memory_usage`, `memory_percent`. Format `sample`: `{pengulangan}_{orm}_{operasi}_{vu}`. |

### ⚙️ Konfigurasi

| File | Fungsi |
|------|--------|
| `config.py` | Menyimpan seluruh path input dan output (`PERF_DATA`, `RESOURCE_DATA`, `DESCRIPTIVE_DIR`, `INFERENTIAL_DIR`, `FIGURES_DIR`, `RESOURCE_OUT`). Semua script mengimpor path dari sini, jadi tidak ada path yang ditulis langsung di dalam script. |

### 📈 Script performa — `scripts/performance/`

| Script | Fungsi | Menulis ke |
|--------|--------|-----------|
| `compute_descriptive_stats.py` | Menghitung `n`, rata-rata, median, dan simpangan baku per kombinasi operasi × VU × ORM untuk P95 dan throughput | `outputs/performance/descriptive/` |
| `generate_descriptive_table.py` | Mengubah statistik deskriptif menjadi tabel siap pakai (satu sel berformat `mean (median; std)`, desimal koma). Membaca output script di atas | `outputs/performance/descriptive/` |
| `run_statistical_analysis.py` | Uji Friedman untuk 24 skenario, koreksi Holm, lalu Wilcoxon post-hoc pada skenario yang signifikan, lengkap dengan rank-biserial correlation | `outputs/performance/inferential/` |
| `summarize_statistical_results.py` | Merangkum hasil Friedman dan Wilcoxon: berapa pasangan signifikan per skenario, dan versi detail yang menggabung keduanya. Membaca output script di atas | `outputs/performance/inferential/` |
| `visualize_p95_line.py` | Grafik garis rata-rata ± simpangan baku P95 latency per operasi (2×2) | `outputs/performance/figures/` |
| `visualize_throughput_line.py` | Sama seperti di atas, untuk throughput | `outputs/performance/figures/` |
| `visualize_p95_boxplot.py` | Boxplot distribusi P95 per ORM dan VU (dua gambar: read+create, join+groupby) | `outputs/performance/figures/` |
| `visualize_throughput_boxplot.py` | Sama seperti di atas, untuk throughput | `outputs/performance/figures/` |

### 🖥️ Script resource — `scripts/resource/`

| Script | Fungsi | Menulis ke |
|--------|--------|-----------|
| `analyze_resource.py` | Mengonversi penggunaan memori ke MiB, membuang data warm-up (`discard`) dan pembacaan pertama tiap sampel (baseline sebelum beban), lalu menghitung rata-rata CPU dan RAM maksimum per sampel dan per ORM × VU | `outputs/resource/` |

### 📤 Output

| File | Isi |
|------|-----|
| `descriptive/p95_descriptive.csv`, `throughput_descriptive.csv` | Statistik deskriptif mentah |
| `descriptive/p95_table.csv`, `throughput_table.csv` | Tabel format laporan |
| `inferential/friedman_results.csv` | Hasil uji omnibus: statistik, p-value, Kendall's W, p-value terkoreksi Holm |
| `inferential/wilcoxon_posthoc_results.csv` | Hasil per pasangan ORM: statistik, p-value, selisih rata-rata/median, W+, W−, rank-biserial, p-value terkoreksi |
| `inferential/inferential_summary.csv` | Satu baris per skenario Friedman, beserta status post-hoc |
| `inferential/inferential_summary_detailed.csv` | Baris Wilcoxon yang digabung dengan hasil Friedman skenarionya |
| `figures/p95_line.png`, `throughput_line.png` | Grafik garis |
| `figures/p95_boxplot_*.png`, `throughput_boxplot_*.png` | Boxplot (`read_create` dan `join_groupby`) |
| `resource/resource_per_sample.csv` | CPU dan RAM per sampel |
| `resource/resource_summary.csv` | CPU dan RAM rata-rata per ORM × VU (sumber Tabel X di artikel) |

---

## 🛠️ 3. Setup

Membutuhkan **Python 3.11+**.

```bash
git clone https://github.com/WahyuPratama222/nestjs-orm-benchmark-analysis.git
cd nestjs-orm-benchmark-analysis

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Versi paket dikunci di `requirements.txt` agar hasil perhitungan (terutama p-value dari SciPy) sama persis dengan yang ada di laporan.

---

## 🚀 4. Menjalankan Analisis

Semua perintah dijalankan **dari root repository** dengan `python -m`, supaya `config.py` ikut terbaca.

```bash
# Performa — statistik deskriptif
python -m scripts.performance.compute_descriptive_stats
python -m scripts.performance.generate_descriptive_table

# Performa — uji inferensial (urutan penting)
python -m scripts.performance.run_statistical_analysis
python -m scripts.performance.summarize_statistical_results

# Performa — visualisasi
python -m scripts.performance.visualize_p95_line
python -m scripts.performance.visualize_throughput_line
python -m scripts.performance.visualize_p95_boxplot
python -m scripts.performance.visualize_throughput_boxplot

# Resource
python -m scripts.resource.analyze_resource
```

**Urutan yang harus dipatuhi:**

1. `generate_descriptive_table` membaca output `compute_descriptive_stats`.
2. `summarize_statistical_results` membaca output `run_statistical_analysis`.

Script lain berdiri sendiri dan hanya membaca file di `data/`.

### Hasil yang seharusnya muncul

Setelah `run_statistical_analysis` selesai, ringkasan di terminal harus sama dengan angka di artikel:

| Item | Nilai |
|------|-------|
| Friedman signifikan | 18 dari 24 skenario (semua `read`, `join`, `groupby`; tidak ada `create`) |
| Total uji Wilcoxon | 108 (18 skenario × 6 pasangan) |
| Wilcoxon signifikan | 102 |

---

## 🔬 5. Metode Statistik

| Tahap | Metode |
|-------|--------|
| Uji omnibus | **Friedman test** per skenario (metrik × operasi × VU), 24 skenario, data berpasangan berdasarkan pengulangan (n = 10, k = 4) |
| Ukuran efek omnibus | **Kendall's W** = χ² / (n × (k − 1)) |
| Koreksi pengujian ganda | **Holm** di seluruh 24 uji Friedman, α = 0,05 |
| Post-hoc | **Wilcoxon signed-rank** dua sisi pada 6 pasangan ORM, hanya untuk skenario yang Friedman-nya signifikan; koreksi Holm di dalam tiap skenario |
| Ukuran efek post-hoc | **Rank-biserial correlation** (nilai −1 sampai 1; tanda mengikuti arah selisih A − B) |

> Dengan n = 10 dan uji Wilcoxon eksak dua sisi, p-value terkecil yang mungkin adalah 2/1024 ≈ 0,00195. Jika banyak pasangan menunjukkan nilai itu, artinya kesepuluh pengulangan searah. Untuk membedakan besarnya perbedaan, gunakan rank-biserial dan selisih rata-rata, bukan p-value.

---

## ✅ 6. Verifikasi Hasil (`checks/`)

Folder `scripts/checks/` **bukan bagian pipeline**. Isinya script kecil yang menghitung ulang **satu skenario** (P95, `read`, 10 VU) dengan kode sederhana, untuk dicocokkan dengan baris yang sama di output pipeline utama.

| Script | Dibandingkan dengan |
|--------|---------------------|
| `check_friedman.py` | Kolom `statistic` dan `p_value` di `friedman_results.csv` |
| `check_wilcoxon.py` | Kolom `statistic`, `p_value`, `mean_difference` di `wilcoxon_posthoc_results.csv` |
| `check_rbc.py` | Kolom `w_positive`, `w_negative`, `rank_biserial` di `wilcoxon_posthoc_results.csv` |
| `plot_raw_groupby_100vu.py` | Grafik batang 10 pengulangan Raw SQL, `groupby`, 100 VU (menyimpan `figures/raw_groupby_100vu.png`) |

```bash
python -m scripts.checks.check_friedman
python -m scripts.checks.check_wilcoxon
python -m scripts.checks.check_rbc
python -m scripts.checks.plot_raw_groupby_100vu
```

Bandingkan dengan `p_value` mentah, bukan `p_adjusted_holm`, karena script check tidak melakukan koreksi.

---

<div align="center">
  <sub>Dibuat dan dikembangkan oleh <strong>Wahyu Pratama</strong></sub>
</div>