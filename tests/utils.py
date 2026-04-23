from datetime import datetime


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
    if category_id:
        data["category_id"] = category_id
    
    return client.post(
        "/expenses/",
        json=data,
        headers=auth_headers(token)
    )


def create_category(client, token, name="测试分类", icon=None, color=None):
    data = {"name": name}
    if icon:
        data["icon"] = icon
    if color:
        data["color"] = color
    
    return client.post(
        "/categories/",
        json=data,
        headers=auth_headers(token)
    )


def create_budget(client, token, category_id, amount=1000, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    return client.post(
        "/budgets/",
        json={
            "amount": amount,
            "year": year,
            "month": month,
            "category_id": category_id
        },
        headers=auth_headers(token)
    )
