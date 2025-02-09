import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.book.books import router as book_router
from app.author.authors import router as author_router
from app.user.auth import router as auth_router
from app.book.loan_books import router as loans_router, get_db
from app.models import Base
from app.user.jwt import *

DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "HASAN2008"
ALGORITHM = "HS256"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(book_router)
app.include_router(author_router)
app.include_router(auth_router)
app.include_router(loans_router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def create_jwt_token(role: str, u_id: Optional[int] = 1):
    token = create_access_token(data={"id": u_id, "username": "TestUser", "role": role})
    return token


@pytest.fixture(scope="module")
def test_client():
    client = TestClient(app)
    yield client


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    # Очистка базы данных перед каждым тестом
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def create_depends(test_client):
    print("Create depends...")
    token = create_jwt_token(role="admin")
    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }
    book_data = {
        "title": "Test book",
        "description": "Test description book",
        "publication": "1000-01-01",
        "authors": [1],
        "style": "bok",
        "copies": "6"
    }
    user_data = {
        "username": "TestUser",
        "email": "test@test.ru",
        "password": "test"
    }
    for i in range(3):
        test_client.post(
            "/author/create",
            json=author_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        test_client.post(
            "/book/create",
            json=book_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        user_data["email"] = f"test{i}@test.ru"
        test_client.post(
            "/register",
            json=user_data
        )
    yield


def test_take_book(test_client, create_depends):
    response_take_more_5_books = None
    response_take_non_enough_book = None
    user1 = create_jwt_token(u_id=1, role="reader")
    user2 = create_jwt_token(u_id=2, role="reader")
    user3 = create_jwt_token(u_id=3, role="reader")

    response_take_book = test_client.post(
        "/book/take/1",
        headers={"Authorization": f"Bearer {user1}"}
    )
    for i in range(6):
        response_take_more_5_books = test_client.post(
            "/book/take/2",
            headers={"Authorization": f"Bearer {user2}"}
        )
    for _ in range(5):
        response_take_non_enough_book = test_client.post(
            "/book/take/2",
            headers={"Authorization": f"Bearer {user3}"}
        )
    response_take_non_exists_book = test_client.post(
        "/book/take/100",
        headers={"Authorization": f"Bearer {user1}"}
    )
    assert response_take_book.status_code == 200, response_take_book.json()
    assert "id" in response_take_book.json()
    assert response_take_book.json()["user_id"] == 1
    assert response_take_book.json()["book_id"] == 1
    assert response_take_book.json()["loan_date"] == str(date.today())
    assert response_take_more_5_books.status_code == 403
    assert response_take_more_5_books.json()["detail"] == "User can't take more than 5 books."
    assert response_take_non_enough_book.status_code == 403
    assert response_take_non_enough_book.json()["detail"] == "Not enough copies of books."
    assert response_take_non_exists_book.status_code == 404


def test_return_book(test_client, create_depends):
    user1 = create_jwt_token(u_id=1, role="reader")
    user2 = create_jwt_token(u_id=2, role="reader")
    test_client.post(
        "/book/take/1",
        headers={"Authorization": f"Bearer {user1}"}
    )
    test_client.post(
        "/book/take/2",
        headers={"Authorization": f"Bearer {user1}"}
    )
    response_return_book = test_client.delete(
        "/book/return/1",
        headers={"Authorization": f"Bearer {user1}"}
    )
    response_non_exists_book = test_client.delete(
        "/book/return/100",
        headers={"Authorization": f"Bearer {user1}"}
    )
    response_non_exists_book_by_user = test_client.delete(
        "/book/return/1",
        headers={"Authorization": f"Bearer {user2}"}
    )

    assert response_return_book.status_code == 200
    assert response_return_book.json() == {"detail": "Returned book", "book_id": 1, "user_id": 1}
    assert response_non_exists_book.status_code == 404
    assert response_non_exists_book.json()["detail"] == "Not found loans by user or book"
    assert response_non_exists_book_by_user.status_code == 404
    assert response_non_exists_book_by_user.json()["detail"] == "Not found loans by user or book"
