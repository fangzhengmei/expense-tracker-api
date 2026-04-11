def create_user_and_login(client, email="test@test.com", password="123456"):
    client.post("/users/register", json={
        "email": email,
        "password": password
    })

    response = client.post("/users/login", json={
        "email": email,
        "password": password
    })

    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_expense(client, token, amount=10, description="test"):
    return client.post(
        "/expenses/",
        json={
            "amount": amount,
            "description": description
        },
        headers=auth_headers(token)
    )