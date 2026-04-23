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


def create_expense(client, token, amount=10, description="test", ledger_id=None, category_id=None):
    data = {
        "amount": amount,
        "description": description
    }
    if ledger_id is not None:
        data["ledger_id"] = ledger_id
    if category_id is not None:
        data["category_id"] = category_id

    return client.post(
        "/expenses/",
        json=data,
        headers=auth_headers(token)
    )


def create_ledger(client, token, name="Test Ledger", ledger_type="shared", description=None):
    data = {
        "name": name,
        "type": ledger_type
    }
    if description:
        data["description"] = description

    response = client.post(
        "/ledgers/",
        json=data,
        headers=auth_headers(token)
    )
    return response


def get_personal_ledger_id(client, token):
    response = client.get(
        "/ledgers/personal",
        headers=auth_headers(token)
    )
    return response.json()["id"]


def create_invitation(client, token, ledger_id, max_uses=None, expires_in_hours=None):
    data = {}
    if max_uses is not None:
        data["max_uses"] = max_uses
    if expires_in_hours is not None:
        data["expires_in_hours"] = expires_in_hours

    response = client.post(
        f"/ledgers/{ledger_id}/invitations",
        json=data,
        headers=auth_headers(token)
    )
    return response


def join_ledger(client, token, code):
    response = client.post(
        "/ledgers/join",
        json={"code": code},
        headers=auth_headers(token)
    )
    return response


def get_ledger_members(client, token, ledger_id):
    response = client.get(
        f"/ledgers/{ledger_id}/members",
        headers=auth_headers(token)
    )
    return response


def update_member_role(client, token, ledger_id, user_id, role):
    response = client.put(
        f"/ledgers/{ledger_id}/members/{user_id}/role",
        json={"role": role},
        headers=auth_headers(token)
    )
    return response


def remove_member(client, token, ledger_id, user_id):
    response = client.delete(
        f"/ledgers/{ledger_id}/members/{user_id}",
        headers=auth_headers(token)
    )
    return response


def get_categories(client, token, ledger_id, category_type=None):
    url = f"/ledgers/{ledger_id}/categories"
    if category_type:
        url += f"?category_type={category_type}"

    response = client.get(
        url,
        headers=auth_headers(token)
    )
    return response


def create_category(client, token, ledger_id, name="Custom Category", category_type="expense", color="#6366F1"):
    response = client.post(
        f"/ledgers/{ledger_id}/categories",
        json={
            "name": name,
            "type": category_type,
            "color": color
        },
        headers=auth_headers(token)
    )
    return response


def update_category(client, token, ledger_id, category_id, name=None, color=None, is_active=None):
    data = {}
    if name:
        data["name"] = name
    if color:
        data["color"] = color
    if is_active is not None:
        data["is_active"] = is_active

    response = client.put(
        f"/ledgers/{ledger_id}/categories/{category_id}",
        json=data,
        headers=auth_headers(token)
    )
    return response


def delete_category(client, token, ledger_id, category_id):
    response = client.delete(
        f"/ledgers/{ledger_id}/categories/{category_id}",
        headers=auth_headers(token)
    )
    return response


def get_category_stats(client, token, ledger_id, category_type="expense"):
    response = client.get(
        f"/ledgers/{ledger_id}/categories/stats?category_type={category_type}",
        headers=auth_headers(token)
    )
    return response


def create_expense_in_ledger(client, token, ledger_id, amount=10, description="test", category_id=None):
    data = {
        "amount": amount,
        "description": description,
        "ledger_id": ledger_id
    }
    if category_id:
        data["category_id"] = category_id

    response = client.post(
        f"/ledgers/{ledger_id}/expenses",
        json=data,
        headers=auth_headers(token)
    )
    return response


def get_ledger_analytics(client, token, ledger_id):
    response = client.get(
        f"/ledgers/{ledger_id}/expenses/analytics",
        headers=auth_headers(token)
    )
    return response
