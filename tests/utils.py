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


def create_expense(client, token, amount=10, description="test", category_id=None):
    data = {
        "amount": amount,
        "description": description
    }
    if category_id is not None:
        data["category_id"] = category_id
    return client.post(
        "/expenses/",
        json=data,
        headers=auth_headers(token)
    )


def create_category(client, token, name="测试分类", icon="📝", color="#6B7280"):
    return client.post(
        "/categories/",
        json={
            "name": name,
            "icon": icon,
            "color": color
        },
        headers=auth_headers(token)
    )


def get_default_categories(client, token):
    response = client.get(
        "/categories/",
        headers=auth_headers(token)
    )
    categories = response.json()
    return [c for c in categories if c["is_default"]]


def get_default_category_id(client, token, name="餐饮"):
    defaults = get_default_categories(client, token)
    for c in defaults:
        if c["name"] == name:
            return c["id"]
    return defaults[0]["id"] if defaults else None