import os
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import (
    get_db,
    Item,
    ClaimRequest,
    Student,
    ActivityLog,
    Notification,
    Admin,
)
from auth import (
    hash_password,
    verify_password,
    login_admin,
    logout_admin,
    get_current_admin,
)

from typing import Optional
from fastapi import File, UploadFile
import shutil
import random
import string
from dotenv import load_dotenv

load_dotenv()

OFFICIAL_WA_NUMBER = os.getenv("OFFICIAL_WA_NUMBER", "6289530428832")

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


def get_admin_or_redirect(request: Request, db: Session):
    admin_id = get_current_admin(request)
    if not admin_id:
        return None
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        return None
    return {"id": admin.id, "username": admin.username}



@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin and verify_password(password, admin.password_hash):
        login_admin(request, admin.id)
        return RedirectResponse("/admin/dashboard", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": "Username/Password salah"}
    )


@router.get("/logout")
async def logout(request: Request):
    logout_admin(request)
    return RedirectResponse("/admin/login", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    # 1. Statistik Dasar
    total_items = db.query(Item).count()
    pending_claims = (
        db.query(ClaimRequest).filter(ClaimRequest.status == "PENDING").count()
    )
    pending_reviews = db.query(Item).filter(Item.is_approved == False).count()

    # 2. Ambil semua data barang untuk ditampilkan di tabel/grid dashboard
    items = db.query(Item).order_by(Item.created_at.desc()).all()

    # 3. Hitung jumlah untuk Filter Pills (Ini yang tadi bikin Error 500)
    counts = {
        "ALL": total_items,
        "LOST": sum(1 for i in items if i.status == "LOST"),
        "FOUND": sum(1 for i in items if i.status == "FOUND"),
        "CLAIMED": sum(1 for i in items if i.status == "CLAIMED"),
    }

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "total_items": total_items,
            "pending_claims": pending_claims,
            "pending_reviews": pending_reviews,
            "items": items,  # <-- Data daftar barang
            "counts": counts,  # <-- Data jumlah filter
        },
    )


@router.get("/items/new", response_class=HTMLResponse)
async def admin_add_item_page(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)
    return templates.TemplateResponse(
        "admin/add_item.html", {"request": request, "admin": admin}
    )


@router.post("/items/new")
async def admin_add_item_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    status: str = Form(...),
    reporter_name: str = Form(...),
    reporter_contact: Optional[str] = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    if not reporter_contact:
        final_contact = OFFICIAL_WA_NUMBER
    else:
        final_contact = reporter_contact

    item_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    image_url = None

    if image and image.filename:
        os.makedirs("uploads/images", exist_ok=True)
        file_path = f"uploads/images/{item_code}_{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/{file_path}"

    new_item = Item(
        code=item_code,
        title=title,
        description=description,
        location=location,
        status=status,
        image_url=image_url,
        reporter_name=reporter_name,
        reporter_contact=final_contact,
        is_approved=True,
    )
    db.add(new_item)
    db.add(
        ActivityLog(
            activity_type="ADD_ITEM",
            description=f"Admin menambahkan barang baru: '{title}' ({item_code})",
        )
    )
    db.commit()
    return RedirectResponse("/admin/dashboard?success=item_created", status_code=303)


@router.get("/claims", response_class=HTMLResponse)
async def admin_claims_list(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    claims = db.query(ClaimRequest).filter(ClaimRequest.status == "PENDING").all()
    claims_data = []
    for claim in claims:
        item = db.query(Item).filter(Item.id == claim.item_id).first()
        if item:
            claims_data.append((claim, item))

    return templates.TemplateResponse(
        "admin/claims_list.html",
        {"request": request, "admin": admin, "claims_data": claims_data},
    )


@router.get("/reviews", response_class=HTMLResponse)
async def admin_reviews(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    items = db.query(Item).filter(Item.is_approved == False).all()
    return templates.TemplateResponse(
        "admin/reviews.html", {"request": request, "admin": admin, "items": items}
    )


@router.get("/history", response_class=HTMLResponse)
async def admin_history(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()
    return templates.TemplateResponse(
        "admin/history.html", {"request": request, "admin": admin, "logs": logs}
    )


@router.get("/item/{item_id}", response_class=HTMLResponse)
async def admin_item_detail(
    request: Request, item_id: int, db: Session = Depends(get_db)
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    # Ambil barang tanpa filter is_approved (karena admin boleh lihat yang belum di-approve)
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    return templates.TemplateResponse(
        "admin/item_detail.html", {"request": request, "admin": admin, "item": item}
    )


# ─── LOGIKA & PROSES (HARD FALLBACK RFID & NOTIFIKASI) ───


@router.post("/claims/{claim_id}/process")
async def process_claim(
    request: Request,
    claim_id: int,
    action: str = Form(...),
    rfid_uid: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    claim = db.query(ClaimRequest).filter(ClaimRequest.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Klaim tidak ditemukan")

    item = db.query(Item).filter(Item.id == claim.item_id).first()

    if action == "approve":
        if not rfid_uid:
            return RedirectResponse("/admin/claims?error=rfid_empty", status_code=303)

        rfid_uid = rfid_uid.strip()
        student = db.query(Student).filter(Student.rfid_uid == rfid_uid).first()

        if not student:
            return RedirectResponse(
                "/admin/claims?error=rfid_not_found", status_code=303
            )

        desc = f"Klaim #{claim.id} disetujui. Barang '{item.title}' diserahkan kepada {student.name} ({student.grade_class}) - NIS: {student.nis} via RFID."
        claim.status = "APPROVED"
        claim.rfid_uid = rfid_uid
        if item:
            item.status = "CLAIMED"

        db.add(ActivityLog(activity_type="APPROVE_CLAIM", description=desc))
        db.commit()
        return RedirectResponse(
            "/admin/claims?success=claim_processed", status_code=303
        )

    elif action == "reject":
        desc = f"Klaim #{claim.id} atas barang '{item.title}' dari {claim.claimer_name} ditolak."
        if claim.proof_image_url:
            old_path = claim.proof_image_url.lstrip("/")
            if os.path.exists(old_path):
                os.remove(old_path)
        db.delete(claim)
        db.add(ActivityLog(activity_type="REJECT_CLAIM", description=desc))
        db.commit()
        return RedirectResponse(
            "/admin/claims?success=reject_processed", status_code=303
        )


@router.post("/reviews/{item_id}/process")
async def process_review(
    request: Request,
    item_id: int,
    action: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    item = db.query(Item).filter(Item.id == item_id, Item.is_approved == False).first()
    if item:
        if action == "approve":
            item.is_approved = True
            db.add(
                ActivityLog(
                    activity_type="APPROVE_REPORT",
                    description=f"Laporan publik disetujui: '{item.title}' ({item.code}).",
                )
            )
        elif action == "reject":
            db.add(
                ActivityLog(
                    activity_type="REJECT_REPORT",
                    description=f"Laporan publik ditolak: '{item.title}'.",
                )
            )
            if item.image_url:
                old_path = item.image_url.lstrip("/")
                if os.path.exists(old_path):
                    os.remove(old_path)
            db.delete(item)
        db.commit()

    return RedirectResponse("/admin/reviews?success=review_processed", status_code=303)


@router.get("/api/notifications")
async def get_notifications(request: Request, db: Session = Depends(get_db)):
    admin_id = get_current_admin(request)
    if not admin_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    notifs = (
        db.query(Notification)
        .filter(Notification.is_read == False)
        .order_by(Notification.created_at.desc())
        .all()
    )
    data = [{"id": n.id, "message": n.message, "link": n.link} for n in notifs]
    return {"unread_count": len(data), "notifications": data}


@router.post("/api/notifications/read")
async def mark_notifications_read(request: Request, db: Session = Depends(get_db)):
    admin_id = get_current_admin(request)
    if not admin_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    db.query(Notification).filter(Notification.is_read == False).update(
        {"is_read": True}
    )
    db.commit()
    return {"status": "success"}

