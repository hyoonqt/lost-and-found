from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db, Item, Admin, ClaimRequest
from auth import hash_password, verify_password, login_admin, logout_admin, get_current_admin
from utils import generate_item_code
from typing import Optional
import aiofiles
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_admin_or_redirect(request: Request, db: Session):
    admin_id = get_current_admin(request)
    if not admin_id:
        return None
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    return admin



@router.get("/login")
async def login_page(request: Request):
    admin_id = get_current_admin(request)
    if admin_id:
        return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Username atau password salah."},
        )
    login_admin(request, admin.id)
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    logout_admin(request)
    return RedirectResponse("/", status_code=302)


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    items = db.query(Item).order_by(Item.created_at.desc()).all()
    counts = {
        "ALL": len(items),
        "LOST": sum(1 for i in items if i.status == "LOST"),
        "FOUND": sum(1 for i in items if i.status == "FOUND"),
        "CLAIMED": sum(1 for i in items if i.status == "CLAIMED"),
    }

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "admin": admin, "items": items, "counts": counts},
    )


# ── Create Item ────────────────────────────────────────────────────────────────

@router.get("/items/new")
async def new_item_page(request: Request, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    preview_code = generate_item_code(db)
    return templates.TemplateResponse(
        "admin/item_form.html",
        {"request": request, "admin": admin, "item": None, "preview_code": preview_code},
    )


@router.post("/items/new")
async def create_item(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form("FOUND"),
    location: str = Form(""),
    reporter_name: str = Form(""),
    image: Optional[UploadFile] = File(None),
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    image_url = None
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            ext = ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        async with aiofiles.open(filepath, "wb") as f:
            content = await image.read()
            await f.write(content)
        image_url = f"/uploads/images/{filename}"

    code = generate_item_code(db)
    item = Item(
        code=code,
        title=title,
        description=description,
        status=status,
        location=location,
        reporter_name=reporter_name,
        image_url=image_url,
    )
    db.add(item)
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/items/{item_id}/edit")
async def edit_item_page(request: Request, item_id: int, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return RedirectResponse("/admin/dashboard", status_code=302)

    return templates.TemplateResponse(
        "admin/item_form.html",
        {"request": request, "admin": admin, "item": item, "preview_code": item.code},
    )


@router.post("/items/{item_id}/edit")
async def update_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form("FOUND"),
    location: str = Form(""),
    reporter_name: str = Form(""),
    image: Optional[UploadFile] = File(None),
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return RedirectResponse("/admin/dashboard", status_code=302)

    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            ext = ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        async with aiofiles.open(filepath, "wb") as f:
            content = await image.read()
            await f.write(content)
        # Remove old image
        if item.image_url:
            old_path = item.image_url.lstrip("/")
            if os.path.exists(old_path):
                os.remove(old_path)
        item.image_url = f"/uploads/images/{filename}"

    item.title = title
    item.description = description
    item.status = status
    item.location = location
    item.reporter_name = reporter_name
    item.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)


# ── Delete Item ────────────────────────────────────────────────────────────────

@router.post("/items/{item_id}/delete")
async def delete_item(request: Request, item_id: int, db: Session = Depends(get_db)):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if item:
        if item.image_url:
            old_path = item.image_url.lstrip("/")
            if os.path.exists(old_path):
                os.remove(old_path)
        db.delete(item)
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=302)


@router.post("/items/{item_id}/status")
async def update_status(
    request: Request,
    item_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = get_admin_or_redirect(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if item and status in ["LOST", "FOUND", "CLAIMED"]:
        item.status = status
        item.updated_at = datetime.utcnow()
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/claims")
async def list_claims(request: Request, db: Session = Depends(get_db)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login", status_code=303)

    admin = db.query(Admin).filter(Admin.id == admin_id).first()

    # FIX 1: Tambahkan filter PENDING agar yang sudah diapprove/direject hilang
    # FIX 2: Gunakan JOIN dengan tabel Item untuk fitur Preview Barang
    claims_data = (
        db.query(ClaimRequest, Item)
        .join(Item, ClaimRequest.item_id == Item.id)
        .filter(ClaimRequest.status == "PENDING")
        .order_by(ClaimRequest.created_at.desc())
        .all()
    )

    return templates.TemplateResponse("admin/claims_list.html", {
        "request": request, 
        "admin": admin, 
        "claims_data": claims_data 
    })


@router.post("/claims/{claim_id}/process")
async def process_claim(claim_id: int, action: str = Form(...), db: Session = Depends(get_db)):
    claim = db.query(ClaimRequest).filter(ClaimRequest.id == claim_id).first()
    if claim:
        claim.status = "APPROVED" if action == "approve" else "REJECTED"
        if action == "approve":
            item = db.query(Item).filter(Item.id == claim.item_id).first()
            if item: item.status = "CLAIMED"
        db.commit()
    return RedirectResponse("/admin/claims", status_code=303)


# --- REVIEW LAPORAN PUBLIK ---

@router.get("/reviews")
async def review_list(request: Request, db: Session = Depends(get_db)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login", status_code=303)

    # Ambil admin untuk nampilin nama di topbar (kalau ada)
    admin = db.query(Admin).filter(Admin.id == admin_id).first()

    # Ambil semua item yang belum di-approve
    pending_items = db.query(Item).filter(Item.is_approved == False).order_by(Item.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/review_list.html", {
        "request": request, 
        "admin": admin, 
        "items": pending_items
    })

@router.post("/reviews/{item_id}/process")
async def process_review(request: Request, item_id: int, action: str = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("admin_id"):
        return RedirectResponse("/admin/login", status_code=303)
        
    item = db.query(Item).filter(Item.id == item_id, Item.is_approved == False).first()
    if item:
        if action == "approve":
            item.is_approved = True
        elif action == "reject":
            # Hapus file foto jika ditolak
            if item.image_url:
                old_path = item.image_url.lstrip("/")
                if os.path.exists(old_path):
                    import os
                    os.remove(old_path)
            db.delete(item)
        db.commit()
            
    return RedirectResponse("/admin/reviews", status_code=303)