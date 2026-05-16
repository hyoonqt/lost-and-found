"""
seed.py — Populate the database with demo data for testing/presentation.
Run: python seed.py
"""
from database import init_db, SessionLocal, Admin, Item
from auth import hash_password
from utils import generate_item_code
from datetime import datetime, timedelta
import random

ITEMS = [
    {
        "title": "Dompet Kulit Hitam",
        "description": "Dompet kulit warna hitam berisi kartu pelajar atas nama Rizky. Ditemukan di dekat kantin sekolah.",
        "status": "FOUND",
        "location": "Kantin Lt. 1",
        "reporter_name": "Bu Sari (Petugas Kantin)",
    },
    {
        "title": "HP Samsung Galaxy A54",
        "description": "Handphone Samsung warna biru, ada stiker kucing di cover belakang. Layar dalam kondisi baik.",
        "status": "FOUND",
        "location": "Lapangan Basket",
        "reporter_name": "Pak Joko (Penjaga)",
    },
    {
        "title": "Kacamata Minus Bingkai Merah",
        "description": "Kacamata bingkai merah, lensa minus. Kemungkinan jatuh saat olahraga.",
        "status": "LOST",
        "location": "Lapangan Olahraga",
        "reporter_name": "Dewi Kusuma (XII IPA 2)",
    },
    {
        "title": "Tas Ransel Hitam Eiger",
        "description": "Tas ransel merk Eiger warna hitam, ada gantungan kunci berbentuk bintang. Isi: buku dan alat tulis.",
        "status": "CLAIMED",
        "location": "Perpustakaan",
        "reporter_name": "Petugas Perpustakaan",
    },
    {
        "title": "Buku Catatan Matematika",
        "description": "Buku catatan pelajaran Matematika kelas XI. Ada nama 'Ahmad' di sampul depan.",
        "status": "FOUND",
        "location": "Ruang Kelas XI IPS 1",
        "reporter_name": "Pak Budi (Wali Kelas)",
    },
    {
        "title": "Earphone Putih JBL",
        "description": "Earphone wired JBL warna putih, kondisi baik. Ditemukan di laci meja.",
        "status": "FOUND",
        "location": "Ruang Komputer",
        "reporter_name": "Bu Rina (Guru TIK)",
    },
    {
        "title": "Jas Hujan Biru",
        "description": "Jas hujan warna biru tua ukuran L. Ada nama tertulis di bagian dalam leher.",
        "status": "LOST",
        "location": "Parkiran Motor",
        "reporter_name": "Agus Setiawan (X IPA 3)",
    },
    {
        "title": "Kalkulator Scientific Casio",
        "description": "Kalkulator Casio fx-991EX warna hitam. Ditemukan di lantai dekat loker siswa.",
        "status": "CLAIMED",
        "location": "Koridor Loker Lt. 2",
        "reporter_name": "Pak Hendra (Security)",
    },
    {
        "title": "Topi Pramuka",
        "description": "Topi Pramuka standar sekolah, ada inisial 'RD' di dalam topi.",
        "status": "FOUND",
        "location": "Ruang UKS",
        "reporter_name": "Petugas UKS",
    },
    {
        "title": "Power Bank Anker 10000mAh",
        "description": "Power bank merk Anker warna hitam, kapasitas 10000mAh. Kondisi normal.",
        "status": "LOST",
        "location": "Aula Sekolah",
        "reporter_name": "Putri Rahayu (XI IPS 2)",
    },
]


def seed():
    init_db()
    db = SessionLocal()

    try:
        # Clear existing data
        db.query(Item).delete()
        db.query(Admin).delete()
        db.commit()

        # Create admin
        admin = Admin(
            username="admin",
            password_hash=hash_password("admin123"),
        )
        db.add(admin)
        db.commit()
        print("✅ Admin created: username=admin, password=admin123")

        # Create items
        base_date = datetime.now() - timedelta(days=30)
        for i, data in enumerate(ITEMS):
            code = generate_item_code(db)
            offset_days = random.randint(0, 30)
            item = Item(
                code=code,
                title=data["title"],
                description=data["description"],
                status=data["status"],
                location=data["location"],
                reporter_name=data["reporter_name"],
                image_url=None,
                created_at=base_date + timedelta(days=offset_days),
                updated_at=base_date + timedelta(days=offset_days),
            )
            db.add(item)
            db.commit()
            print(f"   ✓ [{code}] {data['title']} — {data['status']}")

        print(f"\n🎉 Seeded {len(ITEMS)} items successfully!")
        print("   Run: python main.py")
        print("   Open: http://localhost:8000")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
