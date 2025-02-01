# reader dashboard
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import get_db, User
from app.user.auth import UserResponse, get_current_user
from app.user.jwt import get_password_hash

router = APIRouter()


@router.put("/profile/update/", response_model=UserResponse)
def update_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user.id).first()

    db_user.email = current_user.email
    db_user.username = current_user.username
    db_user.password = get_password_hash(current_user.password)
    db_user.role = current_user.role
    db.commit()
    db.refresh(db_user)
    return db_user
