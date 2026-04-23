import pytest
from decimal import Decimal
from tests.utils import create_user_and_login, auth_headers, create_expense


def create_expense_with_currency(client, token, amount, currency, description):
    return client.post(
        "/expenses/",
        json={
            "amount": amount,
            "currency": currency,
            "description": description
        },
        headers=auth_headers(token)
    )


def test_analytics_summary_converted(client):
    token = create_user_and_login(client, email="summary_converted@test.com")
    
    create_expense_with_currency(client, token, 100, "CNY", "CNY expense")
    create_expense_with_currency(client, token, 100, "USD", "USD expense")
    
    response = client.get(
        "/expenses/analytics/summary/converted?target_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["target_currency"] == "CNY"
    assert "total_converted" in data
    assert "breakdown" in data
    
    expected_total = 100 + (100 * 7.25)
    assert data["total_converted"] == pytest.approx(expected_total, rel=1e-3)


def test_analytics_summary_converted_default_target(client):
    token = create_user_and_login(client, email="summary_default@test.com")
    
    create_expense_with_currency(client, token, 100, "USD", "USD expense")
    
    response = client.get(
        "/expenses/analytics/summary/converted",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["target_currency"] == "CNY"


def test_analytics_summary_converted_to_usd(client):
    token = create_user_and_login(client, email="summary_usd@test.com")
    
    create_expense_with_currency(client, token, 725, "CNY", "CNY expense")
    
    response = client.get(
        "/expenses/analytics/summary/converted?target_currency=USD",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["target_currency"] == "USD"
    assert data["total_converted"] == pytest.approx(100.0, rel=1e-3)


def test_analytics_summary_converted_unsupported_target(client):
    token = create_user_and_login(client, email="summary_unsupported@test.com")
    
    response = client.get(
        "/expenses/analytics/summary/converted?target_currency=XYZ",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 400


def test_analytics_monthly_converted(client):
    token = create_user_and_login(client, email="monthly_converted@test.com")
    
    create_expense_with_currency(client, token, 100, "CNY", "CNY expense")
    create_expense_with_currency(client, token, 100, "USD", "USD expense")
    
    response = client.get(
        "/expenses/analytics/monthly/converted?target_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 1
    month_data = data[0] if isinstance(data, list) else data.get("data", [{}])[0]
    
    if isinstance(data, list):
        assert "total_converted" in data[0]
        assert "target_currency" in data[0]
        expected_total = 100 + (100 * 7.25)
        assert data[0]["total_converted"] == pytest.approx(expected_total, rel=1e-3)


def test_expenses_with_conversion(client):
    token = create_user_and_login(client, email="with_conversion@test.com")
    
    res = create_expense_with_currency(client, token, 100, "USD", "USD expense")
    
    response = client.get(
        "/expenses/with-conversion?target_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    expenses = response.json()
    
    assert len(expenses) >= 1
    expense = expenses[0] if isinstance(expenses, list) else expenses.get("data", [{}])[0]
    
    assert "original_amount" in expense
    assert "original_currency" in expense
    assert "converted_amount" in expense
    assert "exchange_rate" in expense
    assert expense["converted_amount"] == pytest.approx(725.0, rel=1e-3)


def test_custom_rate_affects_analytics(client):
    token = create_user_and_login(client, email="custom_rate_analytics@test.com")
    
    client.post(
        "/exchange-rates/",
        json={
            "currency": "USD",
            "rate_to_cny": 7.5
        },
        headers=auth_headers(token)
    )
    
    create_expense_with_currency(client, token, 100, "USD", "USD expense")
    
    response = client.get(
        "/expenses/analytics/summary/converted?target_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_converted"] == 750.0


def test_multiple_currencies_analytics(client):
    token = create_user_and_login(client, email="multi_currency@test.com")
    
    create_expense_with_currency(client, token, 100, "CNY", "CNY expense")
    create_expense_with_currency(client, token, 100, "USD", "USD expense")
    create_expense_with_currency(client, token, 100, "EUR", "EUR expense")
    
    response = client.get(
        "/expenses/analytics/summary/converted?target_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    
    expected_total = 100 + (100 * 7.25) + (100 * 7.80)
    assert data["total_converted"] == pytest.approx(expected_total, rel=1e-3)
    assert len(data["breakdown"]) == 3


def test_expense_update_currency(client):
    token = create_user_and_login(client, email="update_currency@test.com")
    
    res = create_expense_with_currency(client, token, 100, "USD", "USD expense")
    expense_id = res.json()["id"]
    
    update_response = client.put(
        f"/expenses/{expense_id}",
        json={
            "currency": "EUR"
        },
        headers=auth_headers(token)
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["currency"] == "EUR"


def test_get_single_expense(client):
    token = create_user_and_login(client, email="get_single@test.com")
    
    res = create_expense_with_currency(client, token, 100, "USD", "USD expense")
    expense_id = res.json()["id"]
    
    response = client.get(
        f"/expenses/{expense_id}",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"
    assert data["amount"] == 100
