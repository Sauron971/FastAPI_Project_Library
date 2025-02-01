from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import Author, Book, get_db
from app.user.auth import check_admin

router = APIRouter()  # admin router


class BookCreate(BaseModel):
    title: str
    description: str
    publication: date
    authors: list[int]
    style: str
    copies: Optional[int] = 1


class AuthorResponse(BaseModel):
    id: int
    name: str
    bio: str | None = None
    bday: date | None = None


class LoanResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    loan_date: date
    return_date: date | None = None


class BookResponse(BaseModel):
    id: int
    title: str
    description: str
    publication: date
    authors: list[AuthorResponse]
    style: str
    copies: int
    loans: list[LoanResponse] | None = None

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda dt: dt.isoformat(),
            list: lambda lst: [item.dict() if isinstance(item, BaseModel) else item for item in
                               lst] if lst is not None else None
        }


@router.post("/book/create", response_model=BookResponse, dependencies=[Depends(check_admin)])
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    try:
        db_authors = db.query(Author).filter(Author.id.in_(book.authors)).all()
        if len(db_authors) != len(book.authors):
            raise HTTPException(status_code=400, detail="Some authors were not found.")

        db_book = Book(title=book.title, description=book.description, publication=book.publication,
                       authors=db_authors, style=book.style, copies=book.copies)
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/book/get", response_model=list[BookResponse])
def get_all_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    books = db.query(Book).offset(skip).limit(limit).all()
    book_responses = []
    for book in books:
        author_responses = [
            AuthorResponse(
                id=author.id,
                name=author.name,
                bio=author.bio,
                bday=author.bday
            )
            for author in book.authors
        ]
        loan_responses = [
            LoanResponse(
                id=loan.id,
                user_id=loan.user_id,
                book_id=loan.book_id,
                loan_date=loan.loan_date,
                due_date=loan.return_date
            )
            for loan in book.loans
        ]
        book_responses.append(
            BookResponse(
                id=book.id,
                title=book.title,
                description=book.description,
                publication=book.publication,
                authors=author_responses,
                style=book.style,
                copies=book.copies,
                loans=loan_responses
            )
        )
    return book_responses


@router.get("/book/get/{book_id}", response_model=BookResponse)
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    author_responses = [
        AuthorResponse(
            id=author.id,
            name=author.name,
            bio=author.bio,
            bday=author.bday
        )
        for author in book.authors
    ]
    loan_responses = [
        LoanResponse(
            id=loan.id,
            user_id=loan.user_id,
            book_id=loan.book_id,
            loan_date=loan.loan_date,
            due_date=loan.return_date
        )
        for loan in book.loans
    ]
    return BookResponse(
        id=book.id,
        title=book.title,
        description=book.description,
        publication=book.publication,
        authors=author_responses,
        style=book.style,
        copies=book.copies,
        loans=loan_responses
    )


@router.put("/book/update/{book_id}", response_model=BookResponse, dependencies=[Depends(check_admin)])
def update_book_by_id(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db_book.title = book.title
    db_book.description = book.description
    db_book.publication = book.publication
    db_book.authors = db.query(Author).filter(Author.id.in_(book.authors)).all()
    db_book.style = book.style
    db_book.copies = book.copies
    db.commit()
    db.refresh(db_book)
    author_responses = [
        AuthorResponse(
            id=author.id,
            name=author.name,
            bio=author.bio,
            bday=author.bday
        )
        for author in db_book.authors
    ]
    loan_responses = [
        LoanResponse(
            id=loan.id,
            user_id=loan.user_id,
            book_id=loan.book_id,
            loan_date=loan.loan_date,
            due_date=loan.return_date
        )
        for loan in db_book.loans
    ]
    return BookResponse(
        id=db_book.id,
        title=db_book.title,
        description=db_book.description,
        publication=db_book.publication,
        authors=author_responses,
        style=db_book.style,
        copies=db_book.copies,
        loans=loan_responses
    )


@router.delete("/book/delete/{book_id}", response_model=dict, dependencies=[Depends(check_admin)])
def delete_book_by_id(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(db_book)
    db.commit()
    return {"detail": "Delete book", "ID": str(db_book.id)}
