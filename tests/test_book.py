import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.book.books import router as book_router, get_db
from app.author.authors import router as author_router
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


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def create_jwt_token(role: str):
    token = create_access_token(data={"id": 1, "username": "testUser", "role": role})
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


def test_create_book(test_client):
    token = create_jwt_token(role="admin")
    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }

    response1 = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_data = {
        "title": "Test book",
        "description": "Test description book",
        "publication": "1000-01-01",
        "authors": [1],
        "style": "bok",
        "copies": "5"
    }

    response = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, response.json()
    assert response.json()["title"] == book_data["title"]
    assert response.json()["description"] == book_data["description"]
    assert response.json()["authors"] == [response1.json()]
    assert response.json()["style"] == book_data["style"]
    assert str(response.json()["copies"]) == book_data["copies"]
    assert "id" in response.json()


def test_create_book_without_admin(test_client):
    admin = create_jwt_token(role="admin")
    token = create_jwt_token(role="reader")
    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }

    response1 = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {admin}"}
    )
    book_data = {
        "title": "Test book",
        "description": "Test description book",
        "publication": "1000-01-01",
        "authors": [1],
        "style": "bok",
        "copies": "5"
    }

    response = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "You don't have admin access"}


def test_get_books(test_client):
    token = create_jwt_token(role="admin")
    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }
    test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    book_data = {
        "title": "Test book",
        "description": "Test description book",
        "publication": "1000-01-01",
        "authors": [1],
        "style": "bok",
        "copies": "5"
    }

    book_resp1 = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_resp2 = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_resp3 = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    response_get_all = test_client.get(
        "/book/get"
    )
    response_get_by_id = test_client.get(
        "/book/get/3"
    )
    response_get_non_exists = test_client.get(
        "/book/get/100"
    )

    assert response_get_all.json() == [book_resp1.json(), book_resp2.json(), book_resp3.json()]
    assert response_get_by_id.json() == book_resp3.json()
    assert response_get_non_exists.status_code == 404


def test_update_book(test_client):
    token = create_jwt_token(role="admin")
    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }

    author_create_r = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_data = {
        "title": "Test book",
        "description": "Test description book",
        "publication": "1000-01-01",
        "authors": [1],
        "style": "bok",
        "copies": "5"
    }

    response_before = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_data = {
        "title": "Test book5",
        "description": "Test description book5",
        "publication": "1005-05-05",
        "authors": [1],
        "style": "bok5",
        "copies": 15
    }
    response_after = test_client.put(
        "/book/update/1",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response_update_non_exists = test_client.put(
        "/book/update/100",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response_after.status_code == 200
    assert response_before.json() != response_after.json()
    assert response_after.json()["title"] == book_data["title"]
    assert response_after.json()["description"] == book_data["description"]
    assert response_after.json()["publication"] == book_data["publication"]
    assert response_after.json()["authors"] == [author_create_r.json()]
    assert response_after.json()["style"] == book_data["style"]
    assert response_after.json()["copies"] == book_data["copies"]
    assert response_update_non_exists.status_code == 404


def test_delete_book(test_client):
    token = create_jwt_token(role="admin")
    reader = create_jwt_token(role="reader")
    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }

    test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_data = {
        "title": "Test book",
        "description": "Test description book",
        "publication": "1000-01-01",
        "authors": [1],
        "style": "bok",
        "copies": "5"
    }

    response_create = test_client.post(
        "/book/create",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response_delete = test_client.delete(
        "/book/delete/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    response_delete_non_exists = test_client.delete(
        "/book/delete/100",
        headers={"Authorization": f"Bearer {token}"}
    )
    response_delete_non_admin = test_client.delete(
        "/book/delete/1",
        headers={"Authorization": f"Bearer {reader}"}
    )
    assert response_delete.json() == {"detail": "Delete book", "ID": "1"}
    assert response_delete_non_exists.status_code == 404
    assert response_delete_non_admin.status_code == 403
