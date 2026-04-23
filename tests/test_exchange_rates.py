import pytest
from decimal import Decimal
from tests.utils import create_user_and_login, auth_headers


def test_get_default_rates(client):
    response = client.get("/exchange-rates/defaults")
    assert response.status_code == 200
    data = response.json()
    assert "default_currency" in data
    assert "default_rates" in data
    assert "supported_currencies" in data
    assert data["default_currency"] == "CNY"
    assert "USD" in data["default_rates"]
    assert "EUR" in data["default_rates"]


def test_list_exchange_rates(client):
    token = create_user_and_login(client, email="rates@test.com")
    
    response = client.get(
        "/exchange-rates/",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "default_currency" in data
    assert "user_default_currency" in data
    assert "rates" in data
    assert len(data["rates"]) > 0
    for rate in data["rates"]:
        assert "currency" in rate
        assert "rate_to_cny" in rate
        assert "is_default" in rate


def test_convert_same_currency(client):
    token = create_user_and_login(client, email="convert1@test.com")
    
    response = client.get(
        "/exchange-rates/convert?amount=100&from_currency=CNY&to_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_amount"] == 100
    assert data["original_currency"] == "CNY"
    assert data["converted_amount"] == 100
    assert data["target_currency"] == "CNY"


def test_convert_usd_to_cny(client):
    token = create_user_and_login(client, email="convert2@test.com")
    
    response = client.get(
        "/exchange-rates/convert?amount=100&from_currency=USD&to_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_amount"] == 100
    assert data["original_currency"] == "USD"
    assert data["target_currency"] == "CNY"
    assert data["converted_amount"] == pytest.approx(725.0, rel=1e-3)


def test_convert_cny_to_usd(client):
    token = create_user_and_login(client, email="convert3@test.com")
    
    response = client.get(
        "/exchange-rates/convert?amount=725&from_currency=CNY&to_currency=USD",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["converted_amount"] == pytest.approx(100.0, rel=1e-3)


def test_convert_unsupported_currency(client):
    token = create_user_and_login(client, email="convert4@test.com")
    
    response = client.get(
        "/exchange-rates/convert?amount=100&from_currency=XYZ&to_currency=CNY",
        headers=auth_headers(token)
    )
    
    assert response.status_code == 400


def test_set_custom_exchange_rate(client):
    token = create_user_and_login(client, email="setrate@test.com")
    
    response = client.post(
        "/exchange-rates/",
        json={
            "currency": "USD",
            "rate_to_cny": 7.5
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"
    assert data["rate_to_cny"] == 7.5
    
    convert_response = client.get(
        "/exchange-rates/convert?amount=100&from_currency=USD&to_currency=CNY",
        headers=auth_headers(token)
    )
    convert_data = convert_response.json()
    assert convert_data["converted_amount"] == 750.0


def test_set_invalid_rate(client):
    token = create_user_and_login(client, email="invalidrate@test.com")
    
    response = client.post(
        "/exchange-rates/",
        json={
            "currency": "USD",
            "rate_to_cny": 0
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 422


def test_set_negative_rate(client):
    token = create_user_and_login(client, email="negativerate@test.com")
    
    response = client.post(
        "/exchange-rates/",
        json={
            "currency": "USD",
            "rate_to_cny": -1
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 422


def test_set_unsupported_currency(client):
    token = create_user_and_login(client, email="unsupported@test.com")
    
    response = client.post(
        "/exchange-rates/",
        json={
            "currency": "XYZ",
            "rate_to_cny": 1.0
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 422


def test_batch_set_rates(client):
    token = create_user_and_login(client, email="batch@test.com")
    
    response = client.post(
        "/exchange-rates/batch",
        json={
            "rates": {
                "USD": 7.5,
                "EUR": 8.0,
                "JPY": 0.05
            }
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    usd_rate = next(r for r in data if r["currency"] == "USD")
    assert usd_rate["rate_to_cny"] == 7.5


def test_delete_custom_rate(client):
    token = create_user_and_login(client, email="delete@test.com")
    
    client.post(
        "/exchange-rates/",
        json={
            "currency": "USD",
            "rate_to_cny": 7.5
        },
        headers=auth_headers(token)
    )
    
    convert_response = client.get(
        "/exchange-rates/convert?amount=100&from_currency=USD&to_currency=CNY",
        headers=auth_headers(token)
    )
    assert convert_response.json()["converted_amount"] == 750.0
    
    delete_response = client.delete(
        "/exchange-rates/USD",
        headers=auth_headers(token)
    )
    assert delete_response.status_code == 200
    
    convert_response2 = client.get(
        "/exchange-rates/convert?amount=100&from_currency=USD&to_currency=CNY",
        headers=auth_headers(token)
    )
    assert convert_response2.json()["converted_amount"] == pytest.approx(725.0, rel=1e-3)


def test_create_expense_with_currency(client):
    token = create_user_and_login(client, email="expense_currency@test.com")
    
    response = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "currency": "USD",
            "description": "Test USD expense"
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"


def test_expense_default_currency(client):
    token = create_user_and_login(client, email="expense_default@test.com")
    
    response = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "description": "Test default currency expense"
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "CNY"


def test_unsupported_currency_expense(client):
    token = create_user_and_login(client, email="expense_unsupported@test.com")
    
    response = client.post(
        "/expenses/",
        json={
            "amount": 100,
            "currency": "XYZ",
            "description": "Test unsupported currency"
        },
        headers=auth_headers(token)
    )
    
    assert response.status_code == 422
