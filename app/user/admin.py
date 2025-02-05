# admin dashboard
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import get_db, User
from app.user.auth import UserResponse, UserUpdate, check_admin
from app.user.jwt import get_password_hash

router = APIRouter(dependencies=[Depends(check_admin)])
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %('
                                                                   'message)s')


@router.get("/admin/users/get", response_model=list[UserResponse])
def get_all_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    db_users = db.query(User).offset(skip).limit(limit).all()
    return db_users


@router.post("/admin/register_new", response_model=UserResponse)
def register_new_user(user: UserUpdate, db: Session = Depends(get_db)):
    if not user.email or not user.password or not user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="The email password and username are not specified.")

    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logging.info(f"Registered new user by admin, ID:{db_user.id}")
    return db_user


@router.put("/admin/update_user/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db_user.email = user.email
    db_user.username = user.username
    db_user.password = get_password_hash(user.password)
    db_user.role = user.role
    db.commit()
    db.refresh(db_user)
    logging.info(f"Updated user by admin, ID:{db_user.id}")
    return db_user
