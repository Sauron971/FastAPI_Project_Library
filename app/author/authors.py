import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import Author, get_db
from app.user.auth import check_admin

router = APIRouter()
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


class AuthorCreate(BaseModel):
    name: str
    bio: str
    bday: date


class AuthorResponse(AuthorCreate):
    id: int

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda dt: dt.isoformat()
        }


# Create author
@router.post("/author/create", response_model=AuthorResponse, dependencies=[Depends(check_admin)])
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    try:
        db_author = Author(name=author.name, bio=author.bio, bday=author.bday)
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
        logging.info(f"Created new author with ID: {db_author.id}")
        return db_author
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Get all authors
@router.get("/author/get", response_model=list[AuthorResponse])
def get_all_authors(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    authors = db.query(Author).offset(skip).limit(limit).all()
    return authors


# Get author by id
@router.get("/author/get/{author_id}", response_model=AuthorResponse)
def get_author_by_id(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


# Update author by id
@router.put("/author/update/{author_id}", response_model=AuthorResponse, dependencies=[Depends(check_admin)])
def update_author_by_id(author_id: int, author: AuthorCreate, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    db_author.name = author.name
    db_author.bio = author.bio
    db_author.bday = author.bday
    db.commit()
    db.refresh(db_author)
    logging.info(f"Updated author with ID: {db_author.id}")
    return db_author


# Delete author by id
@router.delete("/author/delete/{author_id}", response_model=dict, dependencies=[Depends(check_admin)])
def delete_author_by_id(author_id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    db.delete(db_author)
    db.commit()
    logging.info(f"Deleted author with ID: {db_author.id}")
    return {"detail": "Delete author", "ID": str(db_author.id)}
