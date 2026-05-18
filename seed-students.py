from database import SessionLocal, Student, engine, Base


def seed_single_student():
    # Memastikan tabel sudah terbentuk (just in case)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Cek apakah UID sudah terdaftar sebelumnya
    existing = db.query(Student).filter(Student.rfid_uid == "1706315949").first()
    if existing:
        print(f"Siswa dengan UID 1706315949 sudah ada: {existing.name}")
        db.close()
        return

    # Data siswa baru yang disesuaikan dengan UID kamu
    new_student = Student(
        rfid_uid="1706315949",
        nis="12453",
        name="Randi Permana Shidiq",
        grade_class="XI RPL 2",
        contact="089530428832",
    )

    try:
        db.add(new_student)
        db.commit()
        print(
            f"Berhasil menambahkan siswa: {new_student.name} ({new_student.grade_class})"
        )
    except Exception as e:
        db.rollback()
        print(f"Gagal menambahkan data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_single_student()
