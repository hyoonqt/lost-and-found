from fastapi import APIRouter, Depends, Request, Query, Form, HTTPException, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db, Item, ClaimRequest, ActivityLog
from typing import Optional
from utils import generate_item_code
import os
import uuid
import aiofiles


router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads/images"
WHATSAPP_NUMBER = "6289530428832"
ADMIN_NAME = "frizz:"
SCHOOL_NAME = "SMK Negeri 1 Surabaya"


@router.get("/")
async def home(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    q: Optional[str] = None,
):
    query = db.query(Item).filter(Item.is_approved == True)

    if status and status in ["LOST", "FOUND", "CLAIMED"]:
        query = query.filter(Item.status == status)

    if q:
        search = f"%{q}%"
        query = query.filter(
            (Item.title.ilike(search))
            | (Item.description.ilike(search))
            | (Item.code.ilike(search))
            | (Item.location.ilike(search))
        )

    items = query.order_by(Item.created_at.desc()).all()

    counts = {
        "ALL": db.query(Item).count(),
        "LOST": db.query(Item).filter(Item.status == "LOST").count(),
        "FOUND": db.query(Item).filter(Item.status == "FOUND").count(),
        "CLAIMED": db.query(Item).filter(Item.status == "CLAIMED").count(),
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": items,
            "counts": counts,
            "active_status": status or "ALL",
            "search_query": q or "",
            "whatsapp_number": WHATSAPP_NUMBER,
            "admin_name": ADMIN_NAME,
            "school_name": SCHOOL_NAME,
        },
    )


@router.get("/item/{code}")
async def item_detail(request: Request, code: str, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.code == code, Item.is_approved == True).first()
    if not item:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )

    wa_message = f"Halo, saya ingin mengklaim barang dengan kode {item.code} - {item.title}"
    wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={wa_message.replace(' ', '%20')}"

    return templates.TemplateResponse(
        "item_detail.html",
        {
            "request": request,
            "item": item,
            "wa_link": wa_link,
            "admin_name": ADMIN_NAME,
            "school_name": SCHOOL_NAME,
        },
    )


@router.post("/item/{code}/claim")
async def submit_claim(
    code: str,
    claimer_name: str = Form(...),
    claimer_class: str = Form(...),
    contact_number: str = Form(...),
    proof: str = Form(...),
    proof_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(Item.code == code).first()
    if not item:
        raise HTTPException(status_code=404)

    if item.status != "FOUND":
        raise HTTPException(status_code=400, detail="Hanya barang berstatus Ditemukan yang bisa diklaim.")

    image_url = None
    if proof_image and proof_image.filename:
        if not proof_image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File harus berupa gambar")
        
        content = await proof_image.read()
        if len(content) > 2 * 1024 * 1024 : #2MB
            raise HTTPException(status_code=400, detail="Ukuran file maksimal 2 MB")
    
        ext = os.path.splitext(proof_image.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"
        filename = f"claim_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        image_url = f"/uploads/images/{filename}"

    new_claim = ClaimRequest(
        item_id=item.id,
        claimer_name=claimer_name,
        claimer_class=claimer_class,
        contact_number=contact_number,
        proof_description=proof,
        proof_image_url=image_url
    )

    db.add(new_claim)
    db.commit()
    
    return RedirectResponse(url=f"/item/{code}?success=true", status_code=303)


@router.get("/report")
async def report_page(request: Request):
    return templates.TemplateResponse("public_report.html", {"request": request, "school_name": SCHOOL_NAME})
    
    
@router.post("/report")
async def submit_report(
        request: Request,
        title: str = Form(...),
        description: str = Form(""),
        status: str = Form(...),
        location: str = Form(""),
        reporter_name: str = Form(...),
        reporter_contact: str = Form(...),
        image: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db)
    ):
        image_url = None
        if image and image.filename:
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File harus gambar")
            
            ext = os.path.splitext(image.filename)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]: ext = ".jpg"
            filename = f"public_{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)

            async with aiofiles.open(filepath, "wb") as f:
                content = await image.read()
                await f.write(content)
            image_url = f"/uploads/images/{filename}"
        
        code = generate_item_code(db)
        new_item = Item(
            code=code, title=title, description=description, status=status,
            location=location, reporter_name=reporter_name, reporter_contact=reporter_contact,
            image_url=image_url,
            is_approved=False
        )
        db.add(new_item)

        log = ActivityLog(
            activity_type="NEW_REPORT",
            description = f"Laporan publik baru ({status}): '{title}' dilaporkan oleh {reporter_name}"
        )
        db.add(log)
        
        db.commit()
        return RedirectResponse("/?succes=reported", status_code=303)