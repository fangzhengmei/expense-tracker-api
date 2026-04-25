from tests.utils import create_user_and_login, auth_headers, create_expense


def test_create_expense(client):
    token = create_user_and_login(client, email="user1@test.com")

    response = create_expense(client, token)

    assert response.status_code == 200
    assert response.json()["amount"] == 10


def test_get_expenses(client):
    token = create_user_and_login(client, email="user2@test.com")

    create_expense(client, token)

    response = client.get(
        "/expenses/",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_expense(client):
    token = create_user_and_login(client, email="user3@test.com")

    res = create_expense(client, token)
    expense_id = res.json()["id"]

    response = client.put(
        f"/expenses/{expense_id}",
        json={"amount": 20, "description": "updated"},
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["amount"] == 20


def test_delete_expense(client):
    token = create_user_and_login(client, email="user4@test.com")

    res = create_expense(client, token)
    expense_id = res.json()["id"]

    response = client.delete(
        f"/expenses/{expense_id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200


def test_forbidden_access(client):
    token1 = create_user_and_login(client, email="user5@test.com")
    token2 = create_user_and_login(client, email="user6@test.com")

    res = create_expense(client, token1)
    expense_id = res.json()["id"]

    response = client.delete(
        f"/expenses/{expense_id}",
        headers=auth_headers(token2)
    )

    assert response.status_code == 404


def test_monthly_analytics(client):
    token = create_user_and_login(client, email="analytics@test.com")

    # Crear varios gastos
    create_expense(client, token, amount=10)
    create_expense(client, token, amount=20)

    response = client.get(
        "/expenses/analytics/monthly",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["total"] == 30


def test_export_csv(client):
    token = create_user_and_login(client, email="export@test.com")

    create_expense(client, token, amount=10, description="午餐")
    create_expense(client, token, amount=20, description="晚餐")

    response = client.get(
        "/expenses/export/csv",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    csv_content = response.content.decode('utf-8-sig')

    assert "ID" in csv_content
    assert "金额" in csv_content
    assert "描述" in csv_content
    assert "创建时间" in csv_content
    assert "更新时间" in csv_content
    assert "午餐" in csv_content
    assert "晚餐" in csv_content
    assert "10" in csv_content
    assert "20" in csv_content


def test_export_csv_empty(client):
    token = create_user_and_login(client, email="empty_export@test.com")

    response = client.get(
        "/expenses/export/csv",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    csv_content = response.content.decode('utf-8-sig')

    assert "ID" in csv_content
    assert "金额" in csv_content


def test_export_csv_without_token(client):
    response = client.get("/expenses/export/csv")

    assert response.status_code == 401


def test_export_csv_with_invalid_token(client):
    response = client.get(
        "/expenses/export/csv",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
    