import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from database import init_db, SessionLocal, Admin
from auth import hash_password
from routers import public, admin

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

app = FastAPI(
    title="Lost & Found System",
    description="School Lost & Found Management System with IoT-ready endpoints",
    version="1.0.0",
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400)

# Static files
os.makedirs("uploads/images", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static",  StaticFiles(directory="static"),  name="static")

# Routers
app.include_router(public.router)
app.include_router(admin.router)

templates = Jinja2Templates(directory="templates")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.on_event("startup")
async def startup():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(Admin).first():
            db.add(Admin(
                username="admin",
                password_hash=hash_password("admin123"),
            ))
            db.commit()
            print("✅ Default admin created — username: admin  password: admin123")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
