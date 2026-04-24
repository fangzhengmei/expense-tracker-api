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


def test_create_category_empty_name(client):
    token = create_user_and_login(client, email="err_cat_user1@test.com")

    response = client.post(
        "/categories/",
        json={
            "name": "",
            "icon": "📝",
            "color": "#6B7280"
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_create_category_name_too_long(client):
    token = create_user_and_login(client, email="err_cat_user2@test.com")

    long_name = "a" * 51

    response = client.post(
        "/categories/",
        json={
            "name": long_name,
            "icon": "📝",
            "color": "#6B7280"
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_create_category_icon_too_long(client):
    token = create_user_and_login(client, email="err_cat_user3@test.com")

    long_icon = "a" * 21

    response = client.post(
        "/categories/",
        json={
            "name": "测试分类",
            "icon": long_icon,
            "color": "#6B7280"
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_create_category_color_too_long(client):
    token = create_user_and_login(client, email="err_cat_user4@test.com")

    long_color = "#1234567"

    response = client.post(
        "/categories/",
        json={
            "name": "测试分类",
            "icon": "📝",
            "color": long_color
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_update_category_empty_name(client):
    token = create_user_and_login(client, email="err_cat_user5@test.com")

    create_response = create_category(client, token, name="原始名称")
    category_id = create_response.json()["id"]

    response = client.put(
        f"/categories/{category_id}",
        json={"name": ""},
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_update_category_name_too_long(client):
    token = create_user_and_login(client, email="err_cat_user6@test.com")

    create_response = create_category(client, token, name="原始名称")
    category_id = create_response.json()["id"]

    long_name = "a" * 51

    response = client.put(
        f"/categories/{category_id}",
        json={"name": long_name},
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_update_category_icon_too_long(client):
    token = create_user_and_login(client, email="err_cat_user7@test.com")

    create_response = create_category(client, token, name="原始名称")
    category_id = create_response.json()["id"]

    long_icon = "a" * 21

    response = client.put(
        f"/categories/{category_id}",
        json={"icon": long_icon},
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_update_category_color_too_long(client):
    token = create_user_and_login(client, email="err_cat_user8@test.com")

    create_response = create_category(client, token, name="原始名称")
    category_id = create_response.json()["id"]

    long_color = "#1234567"

    response = client.put(
        f"/categories/{category_id}",
        json={"color": long_color},
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_expense_create_invalid_category_id(client):
    token = create_user_and_login(client, email="err_exp_user1@test.com")

    response = create_expense(
        client, token,
        amount=50,
        description="测试",
        category_id=999999
    )

    assert response.status_code == 400
    assert "分类" in response.json().get("detail", "") or "无效" in response.json().get("detail", "")


def test_expense_update_invalid_category_id(client):
    token = create_user_and_login(client, email="err_exp_user2@test.com")

    create_response = create_expense(client, token, amount=50, description="测试")
    expense_id = create_response.json()["id"]

    response = client.put(
        f"/expenses/{expense_id}",
        json={"category_id": 999999},
        headers=auth_headers(token)
    )

    assert response.status_code == 400


def test_expense_filter_by_non_existent_category(client):
    token = create_user_and_login(client, email="err_exp_user3@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=30, description="早餐", category_id=food_category_id)

    response = client.get(
        "/expenses/?category_id=999999",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json() == []


def test_expense_update_negative_category_id(client):
    token = create_user_and_login(client, email="err_exp_user4@test.com")

    create_response = create_expense(client, token, amount=50, description="测试")
    expense_id = create_response.json()["id"]

    response = client.put(
        f"/expenses/{expense_id}",
        json={"category_id": -1},
        headers=auth_headers(token)
    )

    assert response.status_code == 400


def test_stats_start_date_only(client):
    token = create_user_and_login(client, email="stats_boundary1@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/categories/analytics/stats?start_date=2020-01-01T00:00:00",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    stats = response.json()

    food_stats = next((s for s in stats if s["category"]["name"] == "餐饮"), None)
    assert food_stats is not None
    assert food_stats["total_amount"] == 50


def test_stats_end_date_only(client):
    token = create_user_and_login(client, email="stats_boundary2@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/categories/analytics/stats?end_date=2030-12-31T23:59:59",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    stats = response.json()

    food_stats = next((s for s in stats if s["category"]["name"] == "餐饮"), None)
    assert food_stats is not None
    assert food_stats["total_amount"] == 50


def test_stats_dates_swapped_returns_empty(client):
    token = create_user_and_login(client, email="stats_boundary3@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/categories/analytics/stats?start_date=2030-01-01&end_date=2020-01-01",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    stats = response.json()

    food_stats = next((s for s in stats if s["category"]["name"] == "餐饮"), None)
    if food_stats:
        assert food_stats["total_amount"] == 0


def test_stats_invalid_date_format(client):
    token = create_user_and_login(client, email="stats_boundary4@test.com")

    response = client.get(
        "/categories/analytics/stats?start_date=invalid-date",
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_expense_filter_start_date_only(client):
    token = create_user_and_login(client, email="exp_boundary1@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/expenses/?start_date=2020-01-01T00:00:00",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_expense_filter_end_date_only(client):
    token = create_user_and_login(client, email="exp_boundary2@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/expenses/?end_date=2030-12-31T23:59:59",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_expense_filter_dates_swapped_returns_empty(client):
    token = create_user_and_login(client, email="exp_boundary3@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/expenses/?start_date=2030-01-01&end_date=2020-01-01",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json() == []


def test_expense_filter_invalid_date_format(client):
    token = create_user_and_login(client, email="exp_boundary4@test.com")

    response = client.get(
        "/expenses/?start_date=not-a-date",
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_category_id_zero_not_allowed_in_create(client):
    token = create_user_and_login(client, email="zero_cat_user@test.com")

    response = create_expense(
        client, token,
        amount=50,
        description="测试",
        category_id=0
    )

    assert response.status_code == 400


def test_get_non_existent_category_id_stats(client):
    token = create_user_and_login(client, email="stats_nonexistent@test.com")

    food_category_id = get_default_category_id(client, token, "餐饮")
    create_expense(client, token, amount=50, description="测试", category_id=food_category_id)

    response = client.get(
        "/categories/analytics/stats?category_id=999999",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json() == []


def test_create_category_without_icon_color_uses_defaults(client):
    token = create_user_and_login(client, email="default_vals_user@test.com")

    response = client.post(
        "/categories/",
        json={"name": "测试默认值"},
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert data["icon"] == "📝"
    assert data["color"] == "#6B7280"


def test_update_category_partial_fields(client):
    token = create_user_and_login(client, email="partial_update_user@test.com")

    create_response = create_category(
        client, token,
        name="原始名称",
        icon="🍎",
        color="#FF0000"
    )
    category_id = create_response.json()["id"]

    response = client.put(
        f"/categories/{category_id}",
        json={"name": "仅更新名称"},
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "仅更新名称"
    assert data["icon"] == "🍎"
    assert data["color"] == "#FF0000"


def test_delete_non_existent_category(client):
    token = create_user_and_login(client, email="del_nonexistent_user@test.com")

    response = client.delete(
        "/categories/999999",
        headers=auth_headers(token)
    )

    assert response.status_code == 404


def test_update_non_existent_category(client):
    token = create_user_and_login(client, email="update_nonexistent_user@test.com")

    response = client.put(
        "/categories/999999",
        json={"name": "测试"},
        headers=auth_headers(token)
    )

    assert response.status_code == 404


def test_cannot_create_duplicate_category_name(client):
    token = create_user_and_login(client, email="dup_cat_user1@test.com")

    response1 = create_category(client, token, name="我的分类")
    assert response1.status_code == 200

    response2 = create_category(client, token, name="我的分类")
    assert response2.status_code == 400
    assert "已存在" in response2.json().get("detail", "")


def test_cannot_create_category_with_default_name(client):
    token = create_user_and_login(client, email="dup_cat_user2@test.com")

    response = create_category(client, token, name="餐饮")
    assert response.status_code == 400
    assert "已存在" in response.json().get("detail", "")


def test_different_users_can_have_same_category_name(client):
    token1 = create_user_and_login(client, email="dup_cat_user3@test.com")
    token2 = create_user_and_login(client, email="dup_cat_user4@test.com")

    response1 = create_category(client, token1, name="我的分类")
    assert response1.status_code == 200

    response2 = create_category(client, token2, name="我的分类")
    assert response2.status_code == 200

    categories1 = client.get("/categories/", headers=auth_headers(token1)).json()
    categories2 = client.get("/categories/", headers=auth_headers(token2)).json()

    user1_custom = [c for c in categories1 if not c["is_default"]]
    user2_custom = [c for c in categories2 if not c["is_default"]]

    assert len(user1_custom) == 1
    assert len(user2_custom) == 1
    assert user1_custom[0]["name"] == "我的分类"
    assert user2_custom[0]["name"] == "我的分类"
    assert user1_custom[0]["id"] != user2_custom[0]["id"]


def test_cannot_update_category_to_duplicate_name(client):
    token = create_user_and_login(client, email="dup_cat_user5@test.com")

    create_category(client, token, name="分类A")
    response_b = create_category(client, token, name="分类B")
    category_b_id = response_b.json()["id"]

    response = client.put(
        f"/categories/{category_b_id}",
        json={"name": "分类A"},
        headers=auth_headers(token)
    )

    assert response.status_code == 400
    assert "已存在" in response.json().get("detail", "")


def test_cannot_update_category_to_default_name(client):
    token = create_user_and_login(client, email="dup_cat_user6@test.com")

    response = create_category(client, token, name="我的分类")
    category_id = response.json()["id"]

    update_response = client.put(
        f"/categories/{category_id}",
        json={"name": "交通"},
        headers=auth_headers(token)
    )

    assert update_response.status_code == 400
    assert "已存在" in update_response.json().get("detail", "")


def test_can_update_category_to_same_name(client):
    token = create_user_and_login(client, email="dup_cat_user7@test.com")

    response = create_category(client, token, name="我的分类", icon="📝", color="#000000")
    category_id = response.json()["id"]

    update_response = client.put(
        f"/categories/{category_id}",
        json={"name": "我的分类", "icon": "💰", "color": "#FF0000"},
        headers=auth_headers(token)
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "我的分类"
    assert updated["icon"] == "💰"
    assert updated["color"] == "#FF0000"
