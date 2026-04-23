from tests.utils import (
    create_user_and_login,
    auth_headers,
    create_ledger,
    get_personal_ledger_id,
    create_invitation,
    join_ledger,
    get_ledger_members,
    update_member_role,
    remove_member,
    get_categories,
    create_category,
    update_category,
    delete_category,
    get_category_stats,
    create_expense_in_ledger,
    get_ledger_analytics
)


class TestLedgerCRUD:
    """账本 CRUD 测试"""

    def test_create_shared_ledger(self, client):
        """测试创建共享账本"""
        token = create_user_and_login(client, email="ledger1@test.com")

        response = create_ledger(client, token, name="家庭账本", ledger_type="shared")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "家庭账本"
        assert data["type"] == "shared"
        assert data["my_role"] == "owner"
        assert data["member_count"] == 1

    def test_create_personal_ledger_via_api(self, client):
        """测试通过 API 创建个人账本"""
        token = create_user_and_login(client, email="ledger2@test.com")

        response = create_ledger(client, token, name="我的私人账本", ledger_type="personal")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "我的私人账本"
        assert data["type"] == "personal"

    def test_get_user_ledgers(self, client):
        """测试获取用户的账本列表"""
        token = create_user_and_login(client, email="ledger3@test.com")

        create_ledger(client, token, name="账本1", ledger_type="shared")
        create_ledger(client, token, name="账本2", ledger_type="shared")

        response = client.get("/ledgers/", headers=auth_headers(token))

        assert response.status_code == 200
        ledgers = response.json()
        assert len(ledgers) >= 3

    def test_get_ledger_by_id(self, client):
        """测试获取单个账本详情"""
        token = create_user_and_login(client, email="ledger4@test.com")

        create_response = create_ledger(client, token, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = client.get(f"/ledgers/{ledger_id}", headers=auth_headers(token))

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试账本"

    def test_update_ledger(self, client):
        """测试更新账本"""
        token = create_user_and_login(client, email="ledger5@test.com")

        create_response = create_ledger(client, token, name="旧名称", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = client.put(
            f"/ledgers/{ledger_id}",
            json={"name": "新名称", "description": "新描述"},
            headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["description"] == "新描述"

    def test_delete_ledger(self, client):
        """测试删除账本"""
        token = create_user_and_login(client, email="ledger6@test.com")

        create_response = create_ledger(client, token, name="待删除", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = client.delete(f"/ledgers/{ledger_id}", headers=auth_headers(token))

        assert response.status_code == 200
        assert response.json()["message"] == "账本已删除"

        get_response = client.get(f"/ledgers/{ledger_id}", headers=auth_headers(token))
        assert get_response.status_code == 404


class TestLedgerAccessControl:
    """账本权限控制测试"""

    def test_non_member_cannot_access_ledger(self, client):
        """测试非成员无法访问账本"""
        token1 = create_user_and_login(client, email="access1@test.com")
        token2 = create_user_and_login(client, email="access2@test.com")

        create_response = create_ledger(client, token1, name="私有账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = client.get(f"/ledgers/{ledger_id}", headers=auth_headers(token2))
        assert response.status_code == 403

    def test_non_member_cannot_create_expense(self, client):
        """测试非成员无法在账本中添加支出"""
        token1 = create_user_and_login(client, email="access3@test.com")
        token2 = create_user_and_login(client, email="access4@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = client.post(
            f"/ledgers/{ledger_id}/expenses",
            json={"amount": 100, "description": "测试支出", "ledger_id": ledger_id},
            headers=auth_headers(token2)
        )
        assert response.status_code == 403

    def test_member_cannot_delete_ledger(self, client):
        """测试普通成员无法删除账本"""
        token1 = create_user_and_login(client, email="access5@test.com")
        token2 = create_user_and_login(client, email="access6@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        response = client.delete(f"/ledgers/{ledger_id}", headers=auth_headers(token2))
        assert response.status_code == 403


class TestInvitationSystem:
    """邀请码系统测试"""

    def test_create_invitation(self, client):
        """测试创建邀请码"""
        token = create_user_and_login(client, email="invite1@test.com")

        create_response = create_ledger(client, token, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = create_invitation(client, token, ledger_id)

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert len(data["code"]) == 8
        assert data["is_active"] == True

    def test_join_ledger_with_invitation(self, client):
        """测试使用邀请码加入账本"""
        token1 = create_user_and_login(client, email="invite2@test.com")
        token2 = create_user_and_login(client, email="invite3@test.com")

        create_response = create_ledger(client, token1, name="家庭账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_response = join_ledger(client, token2, code)

        assert join_response.status_code == 200
        data = join_response.json()
        assert data["id"] == ledger_id
        assert data["my_role"] == "member"

    def test_invitation_with_max_uses(self, client):
        """测试有使用次数限制的邀请码"""
        token1 = create_user_and_login(client, email="invite4@test.com")
        token2 = create_user_and_login(client, email="invite5@test.com")
        token3 = create_user_and_login(client, email="invite6@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id, max_uses=1)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        join_response2 = join_ledger(client, token3, code)
        assert join_response2.status_code == 400

    def test_invitation_with_expiry(self, client):
        """测试有过期时间的邀请码"""
        token = create_user_and_login(client, email="invite7@test.com")

        create_response = create_ledger(client, token, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        response = create_invitation(client, token, ledger_id, expires_in_hours=24)

        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is not None

    def test_duplicate_join_attempt(self, client):
        """测试重复加入账本"""
        token1 = create_user_and_login(client, email="invite8@test.com")
        token2 = create_user_and_login(client, email="invite9@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        join_response2 = join_ledger(client, token2, code)
        assert join_response2.status_code == 400

    def test_deactivate_invitation(self, client):
        """测试使邀请码失效"""
        token1 = create_user_and_login(client, email="invite10@test.com")
        token2 = create_user_and_login(client, email="invite11@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]
        invitation_id = invite_response.json()["id"]

        client.delete(
            f"/ledgers/{ledger_id}/invitations/{invitation_id}",
            headers=auth_headers(token1)
        )

        join_response = join_ledger(client, token2, code)
        assert join_response.status_code == 404


class TestMemberManagement:
    """成员管理测试"""

    def test_list_ledger_members(self, client):
        """测试获取账本成员列表"""
        token1 = create_user_and_login(client, email="member1@test.com")
        token2 = create_user_and_login(client, email="member2@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        response = get_ledger_members(client, token1, ledger_id)

        assert response.status_code == 200
        members = response.json()
        assert len(members) == 2

    def test_update_member_role_by_owner(self, client):
        """测试所有者更新成员角色"""
        token1 = create_user_and_login(client, email="member3@test.com")
        token2 = create_user_and_login(client, email="member4@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_response = join_ledger(client, token2, code)

        members_response = get_ledger_members(client, token1, ledger_id)
        members = members_response.json()
        member2_id = next(m["user_id"] for m in members if m["role"] == "member")

        response = update_member_role(client, token1, ledger_id, member2_id, "admin")

        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_member_cannot_update_role(self, client):
        """测试普通成员无法更新角色"""
        token1 = create_user_and_login(client, email="member5@test.com")
        token2 = create_user_and_login(client, email="member6@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        response = update_member_role(client, token2, ledger_id, 1, "admin")
        assert response.status_code == 403

    def test_admin_can_manage_members(self, client):
        """测试管理员可以移除成员"""
        token1 = create_user_and_login(client, email="member7@test.com")
        token2 = create_user_and_login(client, email="member8@test.com")
        token3 = create_user_and_login(client, email="member9@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response1 = create_invitation(client, token1, ledger_id)
        join_ledger(client, token2, invite_response1.json()["code"])

        invite_response2 = create_invitation(client, token1, ledger_id)
        join_ledger(client, token3, invite_response2.json()["code"])

        members_response = get_ledger_members(client, token1, ledger_id)
        members = members_response.json()
        member2_id = next(m["user_id"] for m in members if m["user_email"] == "member8@test.com")

        update_member_role(client, token1, ledger_id, member2_id, "admin")

        members_response2 = get_ledger_members(client, token1, ledger_id)
        members2 = members_response2.json()
        member3_id = next(m["user_id"] for m in members2 if m["user_email"] == "member9@test.com")

        response = remove_member(client, token2, ledger_id, member3_id)
        assert response.status_code == 200

    def test_member_can_leave_ledger(self, client):
        """测试成员可以退出账本"""
        token1 = create_user_and_login(client, email="member10@test.com")
        token2 = create_user_and_login(client, email="member11@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_response = join_ledger(client, token2, code)

        members_response = get_ledger_members(client, token1, ledger_id)
        members = members_response.json()
        member2_id = next(m["user_id"] for m in members if m["user_email"] == "member11@test.com")

        response = remove_member(client, token2, ledger_id, member2_id)
        assert response.status_code == 200

        members_response2 = get_ledger_members(client, token1, ledger_id)
        assert len(members_response2.json()) == 1

    def test_owner_cannot_remove_self_if_last_owner(self, client):
        """测试最后一个所有者无法移除自己"""
        token = create_user_and_login(client, email="member12@test.com")

        create_response = create_ledger(client, token, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        members_response = get_ledger_members(client, token, ledger_id)
        members = members_response.json()
        owner_id = members[0]["user_id"]

        response = remove_member(client, token, ledger_id, owner_id)
        assert response.status_code == 400


class TestCategoryManagement:
    """分类管理测试"""

    def test_get_default_categories(self, client):
        """测试获取默认分类"""
        token = create_user_and_login(client, email="cat1@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        response = get_categories(client, token, ledger_id)

        assert response.status_code == 200
        categories = response.json()
        assert len(categories) > 0

    def test_filter_categories_by_type(self, client):
        """测试按类型筛选分类"""
        token = create_user_and_login(client, email="cat2@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        expense_response = get_categories(client, token, ledger_id, category_type="expense")
        income_response = get_categories(client, token, ledger_id, category_type="income")

        assert expense_response.status_code == 200
        assert income_response.status_code == 200

        expense_cats = expense_response.json()
        income_cats = income_response.json()

        assert len(expense_cats) >= 10
        assert len(income_cats) >= 5

    def test_create_custom_category(self, client):
        """测试创建自定义分类"""
        token = create_user_and_login(client, email="cat3@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        response = create_category(
            client, token, ledger_id,
            name="自定义分类",
            category_type="expense",
            color="#FF0000"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "自定义分类"
        assert data["color"] == "#FF0000"
        assert data["is_default"] == False

    def test_update_category(self, client):
        """测试更新分类"""
        token = create_user_and_login(client, email="cat4@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        create_response = create_category(
            client, token, ledger_id,
            name="旧名称",
            color="#0000FF"
        )
        category_id = create_response.json()["id"]

        response = update_category(
            client, token, ledger_id, category_id,
            name="新名称",
            color="#00FF00"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["color"] == "#00FF00"

    def test_delete_category(self, client):
        """测试删除分类"""
        token = create_user_and_login(client, email="cat5@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        create_response = create_category(client, token, ledger_id, name="待删除")
        category_id = create_response.json()["id"]

        response = delete_category(client, token, ledger_id, category_id)

        assert response.status_code == 200

    def test_cannot_delete_default_category(self, client):
        """测试无法删除默认分类"""
        token = create_user_and_login(client, email="cat6@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        categories_response = get_categories(client, token, ledger_id, category_type="expense")
        categories = categories_response.json()
        default_category = next(c for c in categories if c["is_default"])

        response = delete_category(client, token, ledger_id, default_category["id"])
        assert response.status_code == 400

    def test_member_can_view_categories(self, client):
        """测试普通成员可以查看分类"""
        token1 = create_user_and_login(client, email="cat7@test.com")
        token2 = create_user_and_login(client, email="cat8@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        response = get_categories(client, token2, ledger_id)
        assert response.status_code == 200

    def test_member_cannot_create_category(self, client):
        """测试普通成员无法创建分类"""
        token1 = create_user_and_login(client, email="cat9@test.com")
        token2 = create_user_and_login(client, email="cat10@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        response = create_category(client, token2, ledger_id, name="测试分类")
        assert response.status_code == 403


class TestCategoryStats:
    """分类统计测试"""

    def test_category_stats_with_expenses(self, client):
        """测试带支出的分类统计"""
        token = create_user_and_login(client, email="stat1@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        categories_response = get_categories(client, token, ledger_id, category_type="expense")
        categories = categories_response.json()
        food_category = next(c for c in categories if c["name"] == "餐饮")
        transport_category = next(c for c in categories if c["name"] == "交通")

        create_expense_in_ledger(client, token, ledger_id, amount=100, description="午餐", category_id=food_category["id"])
        create_expense_in_ledger(client, token, ledger_id, amount=50, description="晚餐", category_id=food_category["id"])
        create_expense_in_ledger(client, token, ledger_id, amount=30, description="地铁", category_id=transport_category["id"])

        response = get_category_stats(client, token, ledger_id)

        assert response.status_code == 200
        stats = response.json()

        food_stat = next(s for s in stats if s["category_name"] == "餐饮")
        transport_stat = next(s for s in stats if s["category_name"] == "交通")

        assert food_stat["total_amount"] == 150.0
        assert food_stat["count"] == 2
        assert transport_stat["total_amount"] == 30.0
        assert transport_stat["count"] == 1

    def test_category_percentage_calculation(self, client):
        """测试分类占比计算"""
        token = create_user_and_login(client, email="stat2@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        categories_response = get_categories(client, token, ledger_id, category_type="expense")
        categories = categories_response.json()
        food_category = next(c for c in categories if c["name"] == "餐饮")
        transport_category = next(c for c in categories if c["name"] == "交通")

        create_expense_in_ledger(client, token, ledger_id, amount=60, description="午餐", category_id=food_category["id"])
        create_expense_in_ledger(client, token, ledger_id, amount=40, description="地铁", category_id=transport_category["id"])

        response = get_category_stats(client, token, ledger_id)
        stats = response.json()

        food_stat = next(s for s in stats if s["category_name"] == "餐饮")
        transport_stat = next(s for s in stats if s["category_name"] == "交通")

        assert food_stat["percentage"] == 60.0
        assert transport_stat["percentage"] == 40.0

    def test_ledger_analytics_includes_categories(self, client):
        """测试账本统计包含分类统计"""
        token = create_user_and_login(client, email="stat3@test.com")

        personal_ledger_response = client.get("/ledgers/personal", headers=auth_headers(token))
        ledger_id = personal_ledger_response.json()["id"]

        categories_response = get_categories(client, token, ledger_id, category_type="expense")
        categories = categories_response.json()
        food_category = next(c for c in categories if c["name"] == "餐饮")

        create_expense_in_ledger(client, token, ledger_id, amount=100, description="午餐", category_id=food_category["id"])

        response = get_ledger_analytics(client, token, ledger_id)

        assert response.status_code == 200
        data = response.json()

        assert "by_category" in data
        assert len(data["by_category"]) > 0

        food_stat = next(c for c in data["by_category"] if c["category_name"] == "餐饮")
        assert food_stat["total"] == 100.0
        assert food_stat["count"] == 1
        assert food_stat["percentage"] == 100.0

    def test_member_can_view_stats(self, client):
        """测试普通成员可以查看统计"""
        token1 = create_user_and_login(client, email="stat4@test.com")
        token2 = create_user_and_login(client, email="stat5@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        categories_response = get_categories(client, token1, ledger_id, category_type="expense")
        categories = categories_response.json()
        food_category = next(c for c in categories if c["name"] == "餐饮")

        create_expense_in_ledger(client, token1, ledger_id, amount=100, description="午餐", category_id=food_category["id"])

        response = get_category_stats(client, token2, ledger_id)
        assert response.status_code == 200

    def test_stats_include_by_user_and_by_category(self, client):
        """测试统计包含按用户和按分类"""
        token1 = create_user_and_login(client, email="stat6@test.com")
        token2 = create_user_and_login(client, email="stat7@test.com")

        create_response = create_ledger(client, token1, name="测试账本", ledger_type="shared")
        ledger_id = create_response.json()["id"]

        invite_response = create_invitation(client, token1, ledger_id)
        code = invite_response.json()["code"]

        join_ledger(client, token2, code)

        categories_response = get_categories(client, token1, ledger_id, category_type="expense")
        categories = categories_response.json()
        food_category = next(c for c in categories if c["name"] == "餐饮")
        transport_category = next(c for c in categories if c["name"] == "交通")

        create_expense_in_ledger(client, token1, ledger_id, amount=100, description="午餐", category_id=food_category["id"])
        create_expense_in_ledger(client, token2, ledger_id, amount=50, description="地铁", category_id=transport_category["id"])

        response = get_ledger_analytics(client, token1, ledger_id)
        data = response.json()

        assert "by_user" in data
        assert "by_category" in data
        assert len(data["by_user"]) == 2
        assert len(data["by_category"]) >= 2
