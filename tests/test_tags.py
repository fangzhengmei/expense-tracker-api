from tests.utils import create_user_and_login, auth_headers, create_expense


def create_tag(client, token, name="餐饮", color="#FF5733"):
    return client.post(
        "/tags/",
        json={
            "name": name,
            "color": color
        },
        headers=auth_headers(token)
    )


def get_tags(client, token):
    return client.get(
        "/tags/",
        headers=auth_headers(token)
    )


def get_tag(client, token, tag_id):
    return client.get(
        f"/tags/{tag_id}",
        headers=auth_headers(token)
    )


def update_tag(client, token, tag_id, name=None, color=None):
    payload = {}
    if name is not None:
        payload["name"] = name
    if color is not None:
        payload["color"] = color
    return client.put(
        f"/tags/{tag_id}",
        json=payload,
        headers=auth_headers(token)
    )


def delete_tag(client, token, tag_id):
    return client.delete(
        f"/tags/{tag_id}",
        headers=auth_headers(token)
    )


def create_expense_with_tags(client, token, amount=10, description="test", tag_ids=None):
    payload = {
        "amount": amount,
        "description": description
    }
    if tag_ids:
        payload["tag_ids"] = tag_ids
    return client.post(
        "/expenses/",
        json=payload,
        headers=auth_headers(token)
    )


def update_expense_with_tags(client, token, expense_id, tag_ids=None):
    payload = {}
    if tag_ids is not None:
        payload["tag_ids"] = tag_ids
    return client.put(
        f"/expenses/{expense_id}",
        json=payload,
        headers=auth_headers(token)
    )


def get_expenses_by_tags(client, token, tag_ids):
    query_params = "&".join([f"tag_ids={tag_id}" for tag_id in tag_ids])
    return client.get(
        f"/expenses/?{query_params}",
        headers=auth_headers(token)
    )


class TestTagCRUD:
    def test_create_tag(self, client):
        token = create_user_and_login(client, email="tag_test1@test.com")
        
        response = create_tag(client, token, name="餐饮", color="#FF5733")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "餐饮"
        assert data["color"] == "#FF5733"
        assert "id" in data

    def test_create_tag_default_color(self, client):
        token = create_user_and_login(client, email="tag_test2@test.com")
        
        response = client.post(
            "/tags/",
            json={"name": "交通"},
            headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        assert response.json()["color"] == "#6366f1"

    def test_get_tags(self, client):
        token = create_user_and_login(client, email="tag_test3@test.com")
        
        create_tag(client, token, name="餐饮", color="#FF5733")
        create_tag(client, token, name="交通", color="#33FF57")
        
        response = get_tags(client, token)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [tag["name"] for tag in data]
        assert "餐饮" in names
        assert "交通" in names

    def test_get_single_tag(self, client):
        token = create_user_and_login(client, email="tag_test4@test.com")
        
        create_response = create_tag(client, token, name="购物", color="#5733FF")
        tag_id = create_response.json()["id"]
        
        response = get_tag(client, token, tag_id)
        
        assert response.status_code == 200
        assert response.json()["name"] == "购物"

    def test_update_tag_name(self, client):
        token = create_user_and_login(client, email="tag_test5@test.com")
        
        create_response = create_tag(client, token, name="旧名称")
        tag_id = create_response.json()["id"]
        
        update_response = update_tag(client, token, tag_id, name="新名称")
        
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "新名称"

    def test_update_tag_color(self, client):
        token = create_user_and_login(client, email="tag_test6@test.com")
        
        create_response = create_tag(client, token, name="测试", color="#FF0000")
        tag_id = create_response.json()["id"]
        
        update_response = update_tag(client, token, tag_id, color="#00FF00")
        
        assert update_response.status_code == 200
        assert update_response.json()["color"] == "#00FF00"

    def test_delete_tag(self, client):
        token = create_user_and_login(client, email="tag_test7@test.com")
        
        create_response = create_tag(client, token, name="待删除")
        tag_id = create_response.json()["id"]
        
        delete_response = delete_tag(client, token, tag_id)
        
        assert delete_response.status_code == 200
        
        get_response = get_tag(client, token, tag_id)
        assert get_response.status_code == 404


class TestTagExpenseAssociation:
    def test_create_expense_with_single_tag(self, client):
        token = create_user_and_login(client, email="assoc_test1@test.com")
        
        tag_response = create_tag(client, token, name="餐饮")
        tag_id = tag_response.json()["id"]
        
        expense_response = create_expense_with_tags(
            client, token, amount=50, description="午餐", tag_ids=[tag_id]
        )
        
        assert expense_response.status_code == 200
        data = expense_response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == tag_id

    def test_create_expense_with_multiple_tags(self, client):
        token = create_user_and_login(client, email="assoc_test2@test.com")
        
        tag1_response = create_tag(client, token, name="餐饮")
        tag2_response = create_tag(client, token, name="工作餐")
        tag1_id = tag1_response.json()["id"]
        tag2_id = tag2_response.json()["id"]
        
        expense_response = create_expense_with_tags(
            client, token, amount=100, description="商务午餐", tag_ids=[tag1_id, tag2_id]
        )
        
        assert expense_response.status_code == 200
        data = expense_response.json()
        assert len(data["tags"]) == 2
        tag_ids = [t["id"] for t in data["tags"]]
        assert tag1_id in tag_ids
        assert tag2_id in tag_ids

    def test_create_expense_without_tags(self, client):
        token = create_user_and_login(client, email="assoc_test3@test.com")
        
        expense_response = create_expense_with_tags(
            client, token, amount=30, description="无标签支出"
        )
        
        assert expense_response.status_code == 200
        data = expense_response.json()
        assert data["tags"] == [] or data["tags"] is None

    def test_update_expense_add_tags(self, client):
        token = create_user_and_login(client, email="assoc_test4@test.com")
        
        expense_response = create_expense(client, token, amount=20, description="初始支出")
        expense_id = expense_response.json()["id"]
        
        tag_response = create_tag(client, token, name="新标签")
        tag_id = tag_response.json()["id"]
        
        update_response = update_expense_with_tags(client, token, expense_id, tag_ids=[tag_id])
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == tag_id

    def test_update_expense_remove_tags(self, client):
        token = create_user_and_login(client, email="assoc_test5@test.com")
        
        tag_response = create_tag(client, token, name="临时标签")
        tag_id = tag_response.json()["id"]
        
        expense_response = create_expense_with_tags(
            client, token, amount=15, description="带标签支出", tag_ids=[tag_id]
        )
        expense_id = expense_response.json()["id"]
        assert len(expense_response.json()["tags"]) == 1
        
        update_response = update_expense_with_tags(client, token, expense_id, tag_ids=[])
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["tags"] == [] or len(data["tags"]) == 0

    def test_update_expense_replace_tags(self, client):
        token = create_user_and_login(client, email="assoc_test6@test.com")
        
        tag1_response = create_tag(client, token, name="标签1")
        tag2_response = create_tag(client, token, name="标签2")
        tag1_id = tag1_response.json()["id"]
        tag2_id = tag2_response.json()["id"]
        
        expense_response = create_expense_with_tags(
            client, token, amount=25, description="测试", tag_ids=[tag1_id]
        )
        expense_id = expense_response.json()["id"]
        
        update_response = update_expense_with_tags(client, token, expense_id, tag_ids=[tag2_id])
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == tag2_id


class TestTagFiltering:
    def test_filter_expenses_by_single_tag(self, client):
        token = create_user_and_login(client, email="filter_test1@test.com")
        
        tag1_response = create_tag(client, token, name="餐饮")
        tag2_response = create_tag(client, token, name="交通")
        tag1_id = tag1_response.json()["id"]
        tag2_id = tag2_response.json()["id"]
        
        create_expense_with_tags(client, token, amount=50, description="午餐", tag_ids=[tag1_id])
        create_expense_with_tags(client, token, amount=30, description="晚餐", tag_ids=[tag1_id])
        create_expense_with_tags(client, token, amount=20, description="地铁", tag_ids=[tag2_id])
        
        response = get_expenses_by_tags(client, token, [tag1_id])
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        descriptions = [e["description"] for e in data]
        assert "午餐" in descriptions
        assert "晚餐" in descriptions

    def test_filter_expenses_by_multiple_tags(self, client):
        token = create_user_and_login(client, email="filter_test2@test.com")
        
        tag1_response = create_tag(client, token, name="餐饮")
        tag2_response = create_tag(client, token, name="工作餐")
        tag1_id = tag1_response.json()["id"]
        tag2_id = tag2_response.json()["id"]
        
        create_expense_with_tags(client, token, amount=100, description="商务午餐", tag_ids=[tag1_id, tag2_id])
        create_expense_with_tags(client, token, amount=50, description="普通午餐", tag_ids=[tag1_id])
        
        response = get_expenses_by_tags(client, token, [tag1_id, tag2_id])
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "商务午餐"

    def test_filter_expenses_no_match(self, client):
        token = create_user_and_login(client, email="filter_test3@test.com")
        
        tag_response = create_tag(client, token, name="未使用标签")
        tag_id = tag_response.json()["id"]
        
        create_expense(client, token, amount=10, description="无标签支出")
        
        response = get_expenses_by_tags(client, token, [tag_id])
        
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_expenses_without_filter_returns_all(self, client):
        token = create_user_and_login(client, email="filter_test4@test.com")
        
        tag_response = create_tag(client, token, name="测试标签")
        tag_id = tag_response.json()["id"]
        
        create_expense_with_tags(client, token, amount=10, description="带标签", tag_ids=[tag_id])
        create_expense(client, token, amount=20, description="不带标签")
        
        response = client.get("/expenses/", headers=auth_headers(token))
        
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestTagEdgeCases:
    def test_create_duplicate_tag_fails(self, client):
        token = create_user_and_login(client, email="edge_test1@test.com")
        
        create_tag(client, token, name="重复标签")
        
        duplicate_response = create_tag(client, token, name="重复标签")
        
        assert duplicate_response.status_code == 400

    def test_update_to_duplicate_name_fails(self, client):
        token = create_user_and_login(client, email="edge_test2@test.com")
        
        create_tag(client, token, name="标签1")
        tag2_response = create_tag(client, token, name="标签2")
        tag2_id = tag2_response.json()["id"]
        
        update_response = update_tag(client, token, tag2_id, name="标签1")
        
        assert update_response.status_code == 400

    def test_different_users_can_have_same_tag_name(self, client):
        token1 = create_user_and_login(client, email="edge_user1@test.com")
        token2 = create_user_and_login(client, email="edge_user2@test.com")
        
        response1 = create_tag(client, token1, name="共享名称")
        response2 = create_tag(client, token2, name="共享名称")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["id"] != response2.json()["id"]

    def test_user_cannot_access_other_users_tag(self, client):
        token1 = create_user_and_login(client, email="edge_private1@test.com")
        token2 = create_user_and_login(client, email="edge_private2@test.com")
        
        tag_response = create_tag(client, token1, name="私有标签")
        tag_id = tag_response.json()["id"]
        
        get_response = get_tag(client, token2, tag_id)
        
        assert get_response.status_code == 404

    def test_user_cannot_delete_other_users_tag(self, client):
        token1 = create_user_and_login(client, email="edge_delete1@test.com")
        token2 = create_user_and_login(client, email="edge_delete2@test.com")
        
        tag_response = create_tag(client, token1, name="待删除私有")
        tag_id = tag_response.json()["id"]
        
        delete_response = delete_tag(client, token2, tag_id)
        
        assert delete_response.status_code == 404
        
        get_response = get_tag(client, token1, tag_id)
        assert get_response.status_code == 200

    def test_create_expense_with_nonexistent_tag_ignored(self, client):
        token = create_user_and_login(client, email="edge_nonexistent@test.com")
        
        expense_response = create_expense_with_tags(
            client, token, amount=100, description="测试", tag_ids=[999999]
        )
        
        assert expense_response.status_code == 200
        data = expense_response.json()
        assert len(data["tags"]) == 0

    def test_delete_tag_removes_associations(self, client):
        token = create_user_and_login(client, email="edge_cascade@test.com")
        
        tag_response = create_tag(client, token, name="即将删除")
        tag_id = tag_response.json()["id"]
        
        expense_response = create_expense_with_tags(
            client, token, amount=50, description="关联支出", tag_ids=[tag_id]
        )
        expense_id = expense_response.json()["id"]
        assert len(expense_response.json()["tags"]) == 1
        
        delete_tag(client, token, tag_id)
        
        get_expense_response = client.get(
            f"/expenses/",
            headers=auth_headers(token)
        )
        
        assert get_expense_response.status_code == 200
        expenses = get_expense_response.json()
        assert len(expenses) == 1
        assert len(expenses[0]["tags"]) == 0

    def test_tag_stats(self, client):
        token = create_user_and_login(client, email="edge_stats@test.com")
        
        tag_response = create_tag(client, token, name="餐饮")
        tag_id = tag_response.json()["id"]
        
        create_expense_with_tags(client, token, amount=50, description="午餐", tag_ids=[tag_id])
        create_expense_with_tags(client, token, amount=30, description="晚餐", tag_ids=[tag_id])
        
        stats_response = client.get(
            f"/tags/{tag_id}/stats",
            headers=auth_headers(token)
        )
        
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert data["expense_count"] == 2
        assert data["total_amount"] == 80.0

    def test_all_tags_stats(self, client):
        token = create_user_and_login(client, email="edge_allstats@test.com")
        
        tag1_response = create_tag(client, token, name="餐饮")
        tag2_response = create_tag(client, token, name="交通")
        tag1_id = tag1_response.json()["id"]
        tag2_id = tag2_response.json()["id"]
        
        create_expense_with_tags(client, token, amount=50, description="午餐", tag_ids=[tag1_id])
        create_expense_with_tags(client, token, amount=20, description="地铁", tag_ids=[tag2_id])
        
        stats_response = client.get(
            "/tags/stats",
            headers=auth_headers(token)
        )
        
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert len(data) == 2
        
        for tag_stat in data:
            if tag_stat["name"] == "餐饮":
                assert tag_stat["expense_count"] == 1
                assert tag_stat["total_amount"] == 50.0
            elif tag_stat["name"] == "交通":
                assert tag_stat["expense_count"] == 1
                assert tag_stat["total_amount"] == 20.0

    def test_tag_stats_empty(self, client):
        token = create_user_and_login(client, email="edge_emptystats@test.com")
        
        tag_response = create_tag(client, token, name="空标签")
        tag_id = tag_response.json()["id"]
        
        stats_response = client.get(
            f"/tags/{tag_id}/stats",
            headers=auth_headers(token)
        )
        
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert data["expense_count"] == 0
        assert data["total_amount"] == 0.0

    def test_invalid_color_format(self, client):
        token = create_user_and_login(client, email="edge_color@test.com")
        
        response = client.post(
            "/tags/",
            json={"name": "测试", "color": "invalid"},
            headers=auth_headers(token)
        )
        
        assert response.status_code == 422

    def test_tag_name_too_long(self, client):
        token = create_user_and_login(client, email="edge_longname@test.com")
        
        long_name = "a" * 51
        response = client.post(
            "/tags/",
            json={"name": long_name},
            headers=auth_headers(token)
        )
        
        assert response.status_code == 422

    def test_tag_name_empty(self, client):
        token = create_user_and_login(client, email="edge_emptyname@test.com")
        
        response = client.post(
            "/tags/",
            json={"name": ""},
            headers=auth_headers(token)
        )
        
        assert response.status_code == 422
