from datetime import datetime
from sqlalchemy.orm import Session
from database import Item


def generate_item_code(db: Session) -> str:
    year = datetime.now().year
    prefix = f"{year}-"

    last_item = (
        db.query(Item)
        .filter(Item.code.like(f"{prefix}%"))
        .order_by(Item.id.desc())
        .first()
    )

    if last_item:
        last_num = int(last_item.code.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


STATUS_COLORS = {
    "LOST": {"bg": "#FEE2E2", "text": "#B91C1C", "border": "#FECACA"},
    "FOUND": {"bg": "#D1FAE5", "text": "#065F46", "border": "#A7F3D0"},
    "CLAIMED": {"bg": "#E0E7FF", "text": "#3730A3", "border": "#C7D2FE"},
}
