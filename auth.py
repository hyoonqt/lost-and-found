import bcrypt
from fastapi import Request

SESSION_KEY = "admin_id"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_current_admin(request: Request):
    admin_id = request.session.get(SESSION_KEY)
    if not admin_id:
        return None
    return admin_id


def require_admin(request: Request):
    admin_id = get_current_admin(request)
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )
    return admin_id


def login_admin(request: Request, admin_id: int):
    request.session[SESSION_KEY] = admin_id


def logout_admin(request: Request):
    request.session.pop(SESSION_KEY, None)
