import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from app.author.authors import router, get_db
from app.models import Base
from app.user.jwt import *

DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "HASAN2008"
ALGORITHM = "HS256"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(router)


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


def test_create_author_as_admin(test_client):
    token = create_jwt_token(role="admin")

    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }

    response = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, response.json()
    assert response.json()["name"] == author_data["name"]
    assert response.json()["bio"] == author_data["bio"]
    assert response.json()["bday"] == author_data["bday"]
    assert "id" in response.json()


def test_create_author_as_admin_with_bad_data(test_client):
    token = create_jwt_token(role="admin")

    author_data = {
        "name": "Test Author",
        "bio3": "This is a test bio.",
        "bday": "1000-01-01",
        "cock": "kokoko"
    }

    response = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422, response.json()


def test_create_author_without_admin_role(test_client):
    token = create_jwt_token(role="user")

    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01",
    }

    response = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You don't have admin access"}


def test_get_authors(test_client):
    token = create_jwt_token(role="admin")

    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }
    author_data2 = {
        "name": "Test Author2",
        "bio": "This is a test bio.2",
        "bday": "1000-01-02"
    }

    create1_author = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    create2_author = test_client.post(
        "/author/create",
        json=author_data2,
        headers={"Authorization": f"Bearer {token}"}
    )

    response_get_all = test_client.get(
        "/author/get"
    )
    response_get_by_id = test_client.get(
        "/author/get/1"
    )
    response_get_non_exists = test_client.get(
        "/author/get/100"
    )

    assert response_get_all.json() == [create1_author.json(), create2_author.json()]
    assert response_get_by_id.json() == create1_author.json()
    assert response_get_non_exists.status_code == 404


def test_update_author(test_client):
    token = create_jwt_token(role="admin")
    non_admin_token = create_jwt_token(role="reader")

    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }
    create1_author = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    updated_author_data = {
        "name": "Updated Test Author",
        "bio": "BIOOOTest",
        "bday": "1000-05-01"
    }
    response = test_client.put(
        "/author/update/1",
        json=updated_author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response_update_non_exists = test_client.put(
        "/author/update/100",
        json=updated_author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response_update_non_admin = test_client.put(
        "/author/update/100",
        json=updated_author_data,
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.json() != create1_author.json()
    assert response.json()["name"] == updated_author_data["name"]
    assert response.json()["bio"] == updated_author_data["bio"]
    assert response.json()["bday"] == updated_author_data["bday"]
    assert "id" in response.json()
    assert response_update_non_exists.status_code == 404
    assert response_update_non_admin.status_code == 403


def test_delete_author(test_client):
    token = create_jwt_token(role="admin")
    non_admin_token = create_jwt_token(role="reader")

    author_data = {
        "name": "Test Author",
        "bio": "This is a test bio.",
        "bday": "1000-01-01"
    }
    create1_author = test_client.post(
        "/author/create",
        json=author_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response = test_client.delete(
        "author/delete/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    response_delete_non_exists = test_client.delete(
        "author/delete/100",
        headers={"Authorization": f"Bearer {token}"}
    )
    response_delete_non_admin = test_client.delete(
        "author/delete/1",
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.json()["detail"] == "Delete author"
    assert response.json()["ID"] == "1"
    assert response_delete_non_exists.status_code == 404
    assert response_delete_non_admin.status_code == 403
