# Lost & Found System

Sistem barang hilang & temuan berbasis web untuk lingkungan sekolah.

---

# Some things might broke because i did some changes and too lazy to edit the readme :)

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Setup

**1. Clone repo**
```bash
git clone https://github.com/hyoonqt/lost-and-found.git
cd lost-and-found
```

**2. Buat file `.env`**
```bash
cp env_example .env
```
Buka `.env` dan sesuaikan isinya

**3. Jalankan**
```bash
docker compose up --build -d
```

**4. Buka browser**

| URL | Keterangan |
|-----|------------|
| `http://localhost:8000` | Halaman publik |
| `http://localhost:8000/admin/login` | Login admin |
| `http://localhost:8000/docs` | API docs |

Login default: `admin` / `admin123`



---

## Load data contoh (opsional)

```bash
docker compose exec app python seed.py
```

---

## Perintah umum

```bash
# Stop
docker compose down

# Restart tanpa rebuild
docker compose up -d

# Rebuild setelah ada perubahan kode
docker compose up --build -d
```

---

## Konfigurasi

Semua konfigurasi ada di file `.env`. Setelah mengubah `.env`, cukup restart tanpa rebuild:
```bash
docker compose up -d
```

Perubahan pada file Python atau template memerlukan rebuild:
```bash
docker compose up --build -d
```
