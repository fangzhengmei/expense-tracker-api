from tests.utils import (
    create_user_and_login,
    auth_headers,
    create_expense,
    create_category,
    get_default_categories,
    get_default_category_id
)


def test_get_default_categories(client):
    token = create_user_and_login(client, email="cat_user1@test.com")

    response = client.get(
        "/categories/",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    categories = response.json()

    default_categories = [c for c in categories if c["is_default"]]
    assert len(default_categories) == 8

    category_names = [c["name"] for c in default_categories]
    assert "餐饮" in category_names
    assert "交通" in category_names
    assert "住房" in category_names
    assert "购物" in category_names
    assert "娱乐" in category_names
    assert "医疗" in category_names
    assert "教育" in category_names
    assert "其他" in category_names


def test_create_custom_category(client):
    token = create_user_and_login(client, email="cat_user2@test.com")

    response = create_category(
        client, token,
        name="我的分类",
        icon="💰",
        color="#FF5733"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "我的分类"
    assert data["icon"] == "💰"
    assert data["color"] == "#FF5733"
    assert data["is_default"] == False
    assert data["user_id"] is not None


def test_get_categories_includes_custom(client):
    token = create_user_and_login(client, email="cat_user3@test.com")

    create_category(client, token, name="自定义分类1")
    create_category(client, token, name="自定义分类2")

    response = client.get(
        "/categories/",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    categories = response.json()

    default_categories = [c for c in categories if c["is_default"]]
    custom_categories = [c for c in categories if not c["is_default"]]

    assert len(default_categories) == 8
    assert len(custom_categories) == 2


def test_update_custom_category(client):
    token = create_user_and_login(client, email="cat_user4@test.com")

    create_response = create_category(client, token, name="旧名称")
    category_id = create_response.json()["id"]

    update_response = client.put(
        f"/categories/{category_id}",
        json={
            "name": "新名称",
            "icon": "🎯",
            "color": "#00FF00"
        },
        headers=auth_headers(token)
    )

    assert update_response.status_code == 200
    updated = update_response.json()

    assert updated["name"] == "新名称"
    assert updated["icon"] == "🎯"
    assert updated["color"] == "#00FF00"


def test_delete_custom_category(client):
    token = create_user_and_login(client, email="cat_user5@test.com")

    create_response = create_category(client, token, name="待删除分类")
    category_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/categories/{category_id}",
        headers=auth_headers(token)
    )

    assert delete_response.status_code == 200

    get_response = client.get(
        "/categories/",
        headers=auth_headers(token)
    )
    categories = get_response.json()
    category_ids = [c["id"] for c in categories]
    assert category_id not in category_ids


def test_cannot_delete_default_category(client):
    token = create_user_and_login(client, email="cat_user6@test.com")

    default_category_id = get_default_category_id(client, token, "餐饮")

    delete_response = client.delete(
        f"/categories/{default_category_id}",
        headers=auth_headers(token)
    )

    assert delete_response.status_code == 400


def test_cannot_update_default_category(client):
    token = create_user_and_login(client, email="cat_user7@test.com")

    default_category_id = get_default_category_id(client, token, "交通")

    update_response = client.put(
        f"/categories/{default_category_id}",
        json={"name": "修改默认分类"},
        headers=auth_headers(token)
    )

    assert update_response.status_code == 403


def test_user_cannot_access_others_custom_category(client):
    token1 = create_user_and_login(client, email="user_a@test.com")
    token2 = create_user_and_login(client, email="user_b@test.com")

    create_response = create_category(client, token1, name="用户A的分类")
    category_id = create_response.json()["id"]

    update_response = client.put(
        f"/categories/{category_id}",
        json={"name": "用户B尝试修改"},
        headers=auth_headers(token2)
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/categories/{category_id}",
        headers=auth_headers(token2)
    )
    assert delete_response.status_code == 403


def test_create_expense_with_category(client):
    token = create_user_and_login(client, email="exp_cat_user1@test.com")

    category_id = get_default_category_id(client, token, "餐饮")

    response = create_expense(
        client, token,
        amount=50,
        description="午餐",
        category_id=category_id
    )

    assert response.status_code == 200
    data = response.json()

    assert data["category_id"] == category_id
    assert data["category"] is not None
    assert data["category"]["id"] == category_id
    assert data["category"]["name"] == "餐饮"


def test_get_expenses_filter_by_category(client):
    token = create_user_and_login(client, email="exp_cat_user2@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    transport_category_id = get_default_category_id(client, token, "交通")

    create_expense(client, token, amount=30, description="早餐", category_id=food_category_id)
    create_expense(client, token, amount=50, description="午餐", category_id=food_category_id)
    create_expense(client, token, amount=20, description="地铁", category_id=transport_category_id)
    create_expense(client, token, amount=100, description="无分类支出")

    all_response = client.get(
        "/expenses/",
        headers=auth_headers(token)
    )
    assert len(all_response.json()) == 4

    food_response = client.get(
        f"/expenses/?category_id={food_category_id}",
        headers=auth_headers(token)
    )
    food_expenses = food_response.json()
    assert len(food_expenses) == 2
    for e in food_expenses:
        assert e["category_id"] == food_category_id

    transport_response = client.get(
        f"/expenses/?category_id={transport_category_id}",
        headers=auth_headers(token)
    )
    transport_expenses = transport_response.json()
    assert len(transport_expenses) == 1
    assert transport_expenses[0]["category_id"] == transport_category_id


def test_update_expense_category(client):
    token = create_user_and_login(client, email="exp_cat_user3@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    transport_category_id = get_default_category_id(client, token, "交通")

    create_response = create_expense(
        client, token,
        amount=50,
        description="测试",
        category_id=food_category_id
    )
    expense_id = create_response.json()["id"]

    update_response = client.put(
        f"/expenses/{expense_id}",
        json={"category_id": transport_category_id},
        headers=auth_headers(token)
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["category_id"] == transport_category_id
    assert updated["category"]["name"] == "交通"


def test_clear_expense_category(client):
    token = create_user_and_login(client, email="exp_cat_user4@test.com")

    category_id = get_default_category_id(client, token, "餐饮")

    create_response = create_expense(
        client, token,
        amount=50,
        description="测试",
        category_id=category_id
    )
    expense_id = create_response.json()["id"]

    update_response = client.put(
        f"/expenses/{expense_id}",
        json={"category_id": 0},
        headers=auth_headers(token)
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["category_id"] is None
    assert updated["category"] is None


def test_cannot_use_invalid_category(client):
    token = create_user_and_login(client, email="exp_cat_user5@test.com")

    response = create_expense(
        client, token,
        amount=50,
        description="测试",
        category_id=99999
    )

    assert response.status_code == 400


def test_cannot_use_others_custom_category(client):
    token1 = create_user_and_login(client, email="cat_owner@test.com")
    token2 = create_user_and_login(client, email="cat_other@test.com")

    create_response = create_category(client, token1, name="私人分类")
    custom_category_id = create_response.json()["id"]

    response = create_expense(
        client, token2,
        amount=50,
        description="尝试使用他人分类",
        category_id=custom_category_id
    )

    assert response.status_code == 400


def test_category_stats(client):
    token = create_user_and_login(client, email="stats_user1@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    transport_category_id = get_default_category_id(client, token, "交通")

    create_expense(client, token, amount=30, description="早餐", category_id=food_category_id)
    create_expense(client, token, amount=50, description="午餐", category_id=food_category_id)
    create_expense(client, token, amount=20, description="地铁", category_id=transport_category_id)
    create_expense(client, token, amount=100, description="无分类")

    stats_response = client.get(
        "/categories/analytics/stats",
        headers=auth_headers(token)
    )

    assert stats_response.status_code == 200
    stats = stats_response.json()

    food_stats = None
    transport_stats = None

    for s in stats:
        if s["category"]["name"] == "餐饮":
            food_stats = s
        elif s["category"]["name"] == "交通":
            transport_stats = s

    assert food_stats is not None
    assert food_stats["total_amount"] == 80
    assert food_stats["expense_count"] == 2

    assert transport_stats is not None
    assert transport_stats["total_amount"] == 20
    assert transport_stats["expense_count"] == 1


def test_category_stats_filter_by_category(client):
    token = create_user_and_login(client, email="stats_user2@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    transport_category_id = get_default_category_id(client, token, "交通")

    create_expense(client, token, amount=30, description="早餐", category_id=food_category_id)
    create_expense(client, token, amount=50, description="午餐", category_id=food_category_id)
    create_expense(client, token, amount=20, description="地铁", category_id=transport_category_id)

    stats_response = client.get(
        f"/categories/analytics/stats?category_id={food_category_id}",
        headers=auth_headers(token)
    )

    assert stats_response.status_code == 200
    stats = stats_response.json()

    assert len(stats) == 1
    assert stats[0]["category"]["name"] == "餐饮"
    assert stats[0]["total_amount"] == 80
