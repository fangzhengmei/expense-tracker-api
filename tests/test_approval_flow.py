from tests.utils import (
    create_user_and_login, 
    auth_headers, 
    create_expense,
    approve_expense,
    get_monthly_analytics
)


class TestMonthlyAnalyticsByStatus:
    """月度统计按审批状态筛选测试"""

    def test_default_only_approved(self, client):
        """默认只统计已通过的支出"""
        employee_token = create_user_and_login(client, email="emp1@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr1@test.com", role="manager")

        res1 = create_expense(client, employee_token, amount=100)
        expense1_id = res1.json()["id"]
        assert res1.json()["status"] == "pending"

        res2 = create_expense(client, employee_token, amount=200)
        expense2_id = res2.json()["id"]

        res3 = create_expense(client, employee_token, amount=50)
        expense3_id = res3.json()["id"]

        approve_expense(client, manager_token, expense1_id, status="approved")
        approve_expense(client, manager_token, expense2_id, status="rejected")

        response = get_monthly_analytics(client, employee_token)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["total"] == 100

    def test_filter_by_pending(self, client):
        """筛选待审批状态"""
        employee_token = create_user_and_login(client, email="emp2@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr2@test.com", role="manager")

        create_expense(client, employee_token, amount=100)
        res2 = create_expense(client, employee_token, amount=200)
        expense2_id = res2.json()["id"]

        approve_expense(client, manager_token, expense2_id, status="approved")

        response = get_monthly_analytics(client, employee_token, status="pending")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["total"] == 100

    def test_filter_by_rejected(self, client):
        """筛选被拒绝状态"""
        employee_token = create_user_and_login(client, email="emp3@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr3@test.com", role="manager")

        res1 = create_expense(client, employee_token, amount=500)
        expense1_id = res1.json()["id"]
        
        create_expense(client, employee_token, amount=100)

        approve_expense(client, manager_token, expense1_id, status="rejected")

        response = get_monthly_analytics(client, employee_token, status="rejected")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["total"] == 500

    def test_compare_approved_vs_pending(self, client):
        """对比已通过和待审批的月度数据（财务场景）"""
        employee_token = create_user_and_login(client, email="emp4@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr4@test.com", role="manager")

        create_expense(client, employee_token, amount=1000)
        res2 = create_expense(client, employee_token, amount=800)
        expense2_id = res2.json()["id"]
        res3 = create_expense(client, employee_token, amount=200)
        expense3_id = res3.json()["id"]

        approve_expense(client, manager_token, expense2_id, status="approved")
        approve_expense(client, manager_token, expense3_id, status="rejected")

        approved_response = get_monthly_analytics(client, employee_token, status="approved")
        pending_response = get_monthly_analytics(client, employee_token, status="pending")
        rejected_response = get_monthly_analytics(client, employee_token, status="rejected")

        assert approved_response.json()[0]["total"] == 800
        assert pending_response.json()[0]["total"] == 1000
        assert rejected_response.json()[0]["total"] == 200


class TestApprovalPermissions:
    """审批权限测试"""

    def test_employee_cannot_approve(self, client):
        """员工没有审批权限"""
        employee_token = create_user_and_login(client, email="emp_no@test.com", role="employee")
        
        res = create_expense(client, employee_token, amount=100)
        expense_id = res.json()["id"]

        approve_response = approve_expense(client, employee_token, expense_id, status="approved")
        
        assert approve_response.status_code == 403

    def test_cannot_approve_own_expense(self, client):
        """不能审批自己的支出"""
        manager_token = create_user_and_login(client, email="mgr_self@test.com", role="manager")

        res = create_expense(client, manager_token, amount=100)
        expense_id = res.json()["id"]

        approve_response = approve_expense(client, manager_token, expense_id, status="approved")
        
        assert approve_response.status_code == 400
        assert "自己" in approve_response.json()["detail"]


class TestExpenseModificationRules:
    """支出修改规则测试"""

    def test_can_update_pending_expense(self, client):
        """待审批状态可以修改"""
        employee_token = create_user_and_login(client, email="emp_mod@test.com", role="employee")

        res = create_expense(client, employee_token, amount=100, description="old")
        expense_id = res.json()["id"]
        assert res.json()["status"] == "pending"

        update_response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 200, "description": "new"},
            headers=auth_headers(employee_token)
        )

        assert update_response.status_code == 200
        assert update_response.json()["amount"] == 200

    def test_cannot_update_approved_expense(self, client):
        """已通过的支出不能修改"""
        employee_token = create_user_and_login(client, email="emp_blocked@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr_blocked@test.com", role="manager")

        res = create_expense(client, employee_token, amount=100)
        expense_id = res.json()["id"]

        approve_expense(client, manager_token, expense_id, status="approved")

        update_response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 999},
            headers=auth_headers(employee_token)
        )

        assert update_response.status_code == 400

    def test_cannot_delete_approved_expense(self, client):
        """已通过的支出不能删除"""
        employee_token = create_user_and_login(client, email="emp_del@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr_del@test.com", role="manager")

        res = create_expense(client, employee_token, amount=100)
        expense_id = res.json()["id"]

        approve_expense(client, manager_token, expense_id, status="approved")

        delete_response = client.delete(
            f"/expenses/{expense_id}",
            headers=auth_headers(employee_token)
        )

        assert delete_response.status_code == 400


class TestApprovalHistory:
    """审批历史记录测试"""

    def test_approval_creates_history(self, client):
        """审批时创建历史记录"""
        employee_token = create_user_and_login(client, email="emp_hist@test.com", role="employee")
        manager_token = create_user_and_login(client, email="mgr_hist@test.com", role="manager")

        res = create_expense(client, employee_token, amount=500)
        expense_id = res.json()["id"]

        approve_response = approve_expense(
            client, manager_token, expense_id, 
            status="approved", comment="费用合理，同意报销"
        )

        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"
        assert approve_response.json()["comment"] == "费用合理，同意报销"
