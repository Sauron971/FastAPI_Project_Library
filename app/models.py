# models.py
import os
from typing import Type

from pydantic import BaseModel
from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


book_authors = Table('book_authors', Base.metadata,
                     Column('book_id', Integer, ForeignKey('books.id'), primary_key=True),
                     Column('author_id', Integer, ForeignKey('authors.id'), primary_key=True)
                     )


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    READER = "reader"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, index=True)
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), default=UserRole.READER)
    loans = relationship("Loan", back_populates="user")


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bio = Column(String)
    bday = Column(Date)
    books = relationship("Book", secondary=book_authors, back_populates="authors")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    publication = Column(Date)
    authors = relationship("Author", secondary=book_authors, back_populates="books")
    style = Column(String)
    copies = Column(Integer, default=1)
    loans = relationship("Loan", back_populates="book")

    def to_pydantic(self, pydantic_model: Type[BaseModel]) -> BaseModel:
        return pydantic_model.from_orm(self)


class Loan(Base):
    __tablename__ = 'loans'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    loan_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")
