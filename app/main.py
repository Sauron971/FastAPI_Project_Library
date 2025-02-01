# main.py
import os

from fastapi import FastAPI


from app.author import authors
from app.book import books
from app.models import init_db
from app.user import auth, admin
from app.book import loan_books


def include_routers():
    app.include_router(authors.router)
    app.include_router(books.router)
    app.include_router(auth.router)
    app.include_router(loan_books.router)
    app.include_router(admin.router)


app = FastAPI()
if __name__ == "__main__":
    import uvicorn

    include_routers()
    init_db()
    uvicorn.run(app, host="127.0.0.1", port=8000)
