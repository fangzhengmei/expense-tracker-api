def create_user_and_login(client, email="test@test.com", password="123456", role="employee"):
    client.post("/users/register", json={
        "email": email,
        "password": password,
        "role": role
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


def approve_expense(client, token, expense_id, status="approved", comment=None):
    payload = {
        "expense_id": expense_id,
        "status": status
    }
    if comment:
        payload["comment"] = comment

    return client.post(
        "/approvals/approve",
        json=payload,
        headers=auth_headers(token)
    )


def get_monthly_analytics(client, token, status=None):
    url = "/expenses/analytics/monthly"
    if status:
        url = f"{url}?status={status}"
    return client.get(url, headers=auth_headers(token))