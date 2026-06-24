from database import SessionLocal, Student, engine, Base

def seed_students():
    # Memastikan tabel sudah terbentuk
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # List data siswa yang mau dimasukkan
    students_data = [
        {
            "rfid_uid": "1706315949",
            "nis": "12453",
            "name": "Randi",
            "grade_class": "XI RPL 2",
            "contact": "089530428832",
        },
        {
            "rfid_uid": "123",
            "nis": "99999",
            "name": "Zaki Nur Hakim",
            "grade_class": "XI RPL 1",
            "contact": "081200000000",
        }
    ]

    try:
        for data in students_data:
            existing = db.query(Student).filter(Student.rfid_uid == data["rfid_uid"]).first()
            if existing:
                print(f"Siswa dengan UID {data['rfid_uid']} sudah ada: {existing.name}")
                continue

            new_student = Student(**data)
            db.add(new_student)
            print(f"Antre untuk ditambahkan: {new_student.name} ({new_student.grade_class})")

        db.commit()
        print("Selesai! Semua data siswa berhasil di-seed ke database.")
        
    except Exception as e:
        db.rollback()
        print(f"Gagal menambahkan data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_students()