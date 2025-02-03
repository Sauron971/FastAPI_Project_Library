import datetime
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import Loan, get_db, User, Book
from app.user.auth import UserResponse, get_current_user
from app.book.books import BookResponse

router = APIRouter()
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


class LoanCreate(BaseModel):
    user_id: int
    book_id: int
    loan_date: date
    return_date: date


class LoanResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    loan_date: date
    return_date: date
    user: UserResponse
    book: BookResponse


@router.post("/book/take/{book_id}", response_model=LoanResponse)
def take_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    db_loan = Loan(user_id=current_user.id,
                   book_id=book_id,
                   loan_date=date.today(),
                   return_date=date.today() + datetime.timedelta(days=20))

    user_loans = len(db.query(Loan).filter(Loan.user_id == current_user.id).all())
    db_book = db.query(Book).filter(Book.id == book_id).first()
    copies = db_book.copies - 1
    if copies < 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough copies of books.")
    if user_loans >= 5:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User can't take more than 5 books.")
    db.add(db_loan)
    db_book.copies = copies
    db.commit()
    db.refresh(db_loan)
    db.refresh(db_book)
    logging.info(f"{current_user.username} take the book with ID: {book_id}")
    return db_loan


@router.delete("/book/return/{book_id}", response_model=dict)
def return_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    db_loan = db.query(Loan).filter(Loan.user_id == current_user.id,
                                    Loan.book_id == book_id
                                    ).first()
    if not db_loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found loans by user or book")
    db.delete(db_loan)
    db_book = db.query(Book).filter(Book.id == db_loan.book_id).first()
    db_book.copies = db_book.copies + 1
    db.commit()
    db.refresh(db_book)
    logging.info(f"{current_user.username} return the book with ID: {book_id}")
    return {"detail": "Returned book", "book_id": book_id, "user_id": current_user.id}






