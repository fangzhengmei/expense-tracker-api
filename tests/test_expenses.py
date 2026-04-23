from tests.utils import create_user_and_login, auth_headers, create_expense, create_category, create_budget


def test_create_expense(client):
    token = create_user_and_login(client, email="user1@test.com")

    response = create_expense(client, token)

    assert response.status_code == 200
    data = response.json()
    assert data["expense"]["amount"] == 10


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
    expense_id = res.json()["expense"]["id"]

    response = client.put(
        f"/expenses/{expense_id}",
        json={"amount": 20, "description": "updated"},
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["expense"]["amount"] == 20


def test_delete_expense(client):
    token = create_user_and_login(client, email="user4@test.com")

    res = create_expense(client, token)
    expense_id = res.json()["expense"]["id"]

    response = client.delete(
        f"/expenses/{expense_id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200


def test_forbidden_access(client):
    token1 = create_user_and_login(client, email="user5@test.com")
    token2 = create_user_and_login(client, email="user6@test.com")

    res = create_expense(client, token1)
    expense_id = res.json()["expense"]["id"]

    response = client.delete(
        f"/expenses/{expense_id}",
        headers=auth_headers(token2)
    )

    assert response.status_code == 404


def test_monthly_analytics(client):
    token = create_user_and_login(client, email="analytics@test.com")

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


def test_create_category(client):
    token = create_user_and_login(client, email="category_test@test.com")

    response = create_category(client, token, name="餐饮")

    assert response.status_code == 200
    assert response.json()["name"] == "餐饮"


def test_get_categories(client):
    token = create_user_and_login(client, email="categories_test@test.com")

    create_category(client, token, name="餐饮")
    create_category(client, token, name="交通")

    response = client.get(
        "/categories/",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_budget(client):
    token = create_user_and_login(client, email="budget_test@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    budget_res = create_budget(client, token, category_id=category_id, amount=1000)

    assert budget_res.status_code == 200
    assert budget_res.json()["amount"] == 1000


def test_expense_with_budget_check(client):
    token = create_user_and_login(client, email="budget_check@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    create_budget(client, token, category_id=category_id, amount=1000)

    expense_res = client.post(
        "/expenses/",
        json={
            "amount": 200,
            "description": "午餐",
            "category_id": category_id
        },
        headers=auth_headers(token)
    )

    assert expense_res.status_code == 200
    data = expense_res.json()
    
    assert data["expense"]["amount"] == 200
    assert data["budget_info"] is not None
    assert data["budget_info"]["has_budget"] == True
    assert data["budget_info"]["spent"] == 200
    assert data["budget_info"]["remaining"] == 800


def test_budget_summary(client):
    token = create_user_and_login(client, email="budget_summary@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    create_budget(client, token, category_id=category_id, amount=1000)

    client.post(
        "/expenses/",
        json={
            "amount": 300,
            "description": "午餐",
            "category_id": category_id
        },
        headers=auth_headers(token)
    )

    response = client.get(
        "/budgets/summary",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    
    assert data["total_budget"] == 1000
    assert data["total_spent"] == 300
    assert data["total_remaining"] == 700
    assert len(data["budgets"]) == 1


def test_overdue_budgets_empty(client):
    token = create_user_and_login(client, email="overdue_empty@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    create_budget(client, token, category_id=category_id, amount=1000)

    response = client.get(
        "/budgets/overdue",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_overdue_budgets_with_overdue(client):
    token = create_user_and_login(client, email="overdue_test@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    create_budget(client, token, category_id=category_id, amount=500)

    client.post(
        "/expenses/",
        json={
            "amount": 600,
            "description": "聚餐",
            "category_id": category_id
        },
        headers=auth_headers(token)
    )

    response = client.get(
        "/budgets/overdue",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category_name"] == "餐饮"
    assert data[0]["amount"] == 500
    assert data[0]["spent"] == 600
    assert data[0]["remaining"] == -100
    assert data[0]["overdue_amount"] == 100
    assert data[0]["percentage"] == 120.0


def test_overdue_summary(client):
    token = create_user_and_login(client, email="overdue_summary@test.com")

    category1_res = create_category(client, token, name="餐饮")
    category1_id = category1_res.json()["id"]

    category2_res = create_category(client, token, name="娱乐")
    category2_id = category2_res.json()["id"]

    create_budget(client, token, category_id=category1_id, amount=500)
    create_budget(client, token, category_id=category2_id, amount=300)

    client.post(
        "/expenses/",
        json={
            "amount": 600,
            "description": "聚餐",
            "category_id": category1_id
        },
        headers=auth_headers(token)
    )

    client.post(
        "/expenses/",
        json={
            "amount": 400,
            "description": "电影",
            "category_id": category2_id
        },
        headers=auth_headers(token)
    )

    response = client.get(
        "/budgets/overdue/summary",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    
    assert data["total_overdue_count"] == 2
    assert data["total_overdue_amount"] == 200
    assert len(data["overdues"]) == 2


def test_budget_amount_zero(client):
    token = create_user_and_login(client, email="budget_zero@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    budget_res = create_budget(client, token, category_id=category_id, amount=0)

    assert budget_res.status_code == 200
    assert budget_res.json()["amount"] == 0


def test_create_expense_with_nonexistent_category(client):
    token = create_user_and_login(client, email="nonexistent_category@test.com")

    response = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "description": "测试",
            "category_id": 99999
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 400
    assert "不存在" in response.json()["detail"]


def test_create_expense_with_other_users_category(client):
    token1 = create_user_and_login(client, email="user_a@test.com")
    token2 = create_user_and_login(client, email="user_b@test.com")

    category_res = create_category(client, token1, name="用户A的分类")
    category_id = category_res.json()["id"]

    response = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "description": "测试",
            "category_id": category_id
        },
        headers=auth_headers(token2)
    )

    assert response.status_code == 400
    assert "不存在" in response.json()["detail"]


def test_create_budget_with_nonexistent_category(client):
    token = create_user_and_login(client, email="budget_nonexistent_cat@test.com")

    from datetime import datetime
    now = datetime.now()

    response = client.post(
        "/budgets/",
        json={
            "amount": 1000,
            "year": now.year,
            "month": now.month,
            "category_id": 99999
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert "分类不存在" in response.json()["detail"]


def test_create_budget_with_other_users_category(client):
    token1 = create_user_and_login(client, email="user_c@test.com")
    token2 = create_user_and_login(client, email="user_d@test.com")

    category_res = create_category(client, token1, name="用户C的分类")
    category_id = category_res.json()["id"]

    from datetime import datetime
    now = datetime.now()

    response = client.post(
        "/budgets/",
        json={
            "amount": 1000,
            "year": now.year,
            "month": now.month,
            "category_id": category_id
        },
        headers=auth_headers(token2)
    )

    assert response.status_code == 404
    assert "分类不存在" in response.json()["detail"]


def test_duplicate_category_name(client):
    token = create_user_and_login(client, email="duplicate_cat@test.com")

    create_category(client, token, name="餐饮")

    response = create_category(client, token, name="餐饮")

    assert response.status_code == 400
    assert "已存在" in response.json()["detail"]


def test_duplicate_budget(client):
    token = create_user_and_login(client, email="duplicate_budget@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    from datetime import datetime
    now = datetime.now()

    create_budget(client, token, category_id=category_id, amount=1000)

    response = client.post(
        "/budgets/",
        json={
            "amount": 2000,
            "year": now.year,
            "month": now.month,
            "category_id": category_id
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 400
    assert "已存在" in response.json()["detail"]


def test_budget_monthly_list(client):
    token = create_user_and_login(client, email="budget_monthly@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    create_budget(client, token, category_id=category_id, amount=1000)

    client.post(
        "/expenses/",
        json={
            "amount": 300,
            "description": "午餐",
            "category_id": category_id
        },
        headers=auth_headers(token)
    )

    response = client.get(
        "/budgets/monthly",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["amount"] == 1000
    assert data[0]["spent"] == 300
    assert data[0]["remaining"] == 700
    assert data[0]["percentage"] == 30.0


def test_expense_update_with_category_change(client):
    token = create_user_and_login(client, email="expense_cat_change@test.com")

    category1_res = create_category(client, token, name="餐饮")
    category1_id = category1_res.json()["id"]

    category2_res = create_category(client, token, name="交通")
    category2_id = category2_res.json()["id"]

    expense_res = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "description": "午餐",
            "category_id": category1_id
        },
        headers=auth_headers(token)
    )
    expense_id = expense_res.json()["expense"]["id"]

    update_res = client.put(
        f"/expenses/{expense_id}",
        json={
            "category_id": category2_id
        },
        headers=auth_headers(token)
    )

    assert update_res.status_code == 200
    assert update_res.json()["expense"]["category_id"] == category2_id


def test_expense_remove_category(client):
    token = create_user_and_login(client, email="expense_remove_cat@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    expense_res = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "description": "午餐",
            "category_id": category_id
        },
        headers=auth_headers(token)
    )
    expense_id = expense_res.json()["expense"]["id"]

    update_res = client.put(
        f"/expenses/{expense_id}",
        json={
            "category_id": 0
        },
        headers=auth_headers(token)
    )

    assert update_res.status_code == 200
    assert update_res.json()["expense"]["category_id"] is None


def test_get_single_category(client):
    token = create_user_and_login(client, email="single_cat@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    response = client.get(
        f"/categories/{category_id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["name"] == "餐饮"


def test_get_nonexistent_category(client):
    token = create_user_and_login(client, email="nonexistent_cat_get@test.com")

    response = client.get(
        "/categories/99999",
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert "分类不存在" in response.json()["detail"]


def test_update_category(client):
    token = create_user_and_login(client, email="update_cat@test.com")

    category_res = create_category(client, token, name="餐饮")
    category_id = category_res.json()["id"]

    response = client.put(
        f"/categories/{category_id}",
        json={
            "name": "美食",
            "color": "#FF0000"
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["name"] == "美食"
    assert response.json()["color"] == "#FF0000"


def test_delete_category(client):
    token = create_user_and_login(client, email="delete_cat@test.com")

    category_res = create_category(client, token, name="测试分类")
    category_id = category_res.json()["id"]

    response = client.delete(
        f"/categories/{category_id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/categories/{category_id}",
        headers=auth_headers(token)
    )
    assert get_response.status_code == 404


def test_budget_summary_without_budgets(client):
    token = create_user_and_login(client, email="summary_no_budget@test.com")

    response = client.get(
        "/budgets/summary",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_budget"] == 0
    assert data["total_spent"] == 0
    assert data["total_remaining"] == 0
    assert len(data["budgets"]) == 0


def test_overdue_summary_without_overdues(client):
    token = create_user_and_login(client, email="overdue_no_overdues@test.com")

    response = client.get(
        "/budgets/overdue/summary",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_overdue_count"] == 0
    assert data["total_overdue_amount"] == 0
    assert len(data["overdues"]) == 0
