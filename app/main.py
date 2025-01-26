# main.py
from fastapi import FastAPI

from app.author import authors
from app.book import books
from app.models import init_db


app = FastAPI()

app.include_router(authors.router)
app.include_router(books.router)

init_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
