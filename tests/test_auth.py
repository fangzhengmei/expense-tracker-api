def test_register(client):
    response = client.post("/users/register", json={
        "email": "test1@test.com",
        "password": "123456"
    })

    assert response.status_code == 200
    assert response.json()["email"] == "test1@test.com"


def test_login_ok(client):
    client.post("/users/register", json={
        "email": "test2@test.com",
        "password": "123456"
    })

    response = client.post("/users/login", json={
        "email": "test2@test.com",
        "password": "123456"
    })

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    client.post("/users/register", json={
        "email": "test3@test.com",
        "password": "123456"
    })

    response = client.post("/users/login", json={
        "email": "test3@test.com",
        "password": "wrong"
    })

    assert response.status_code == 401


def test_register_duplicate(client):
    client.post("/users/register", json={
        "email": "test4@test.com",
        "password": "123456"
    })

    response = client.post("/users/register", json={
        "email": "test4@test.com",
        "password": "123456"
    })

    assert response.status_code == 400