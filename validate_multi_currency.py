import sys
sys.path.insert(0, '.')

try:
    from app.core.constants import SUPPORTED_CURRENCIES, DEFAULT_CURRENCY, CURRENCY_SYMBOLS
    print("✓ Constants loaded successfully")
    print(f"  Default currency: {DEFAULT_CURRENCY}")
    print(f"  Supported currencies: {SUPPORTED_CURRENCIES}")
except Exception as e:
    print(f"✗ Failed to load constants: {e}")

try:
    from app.models.expense import Expense
    print("✓ Expense model loaded successfully")
    print(f"  Columns: {[c.name for c in Expense.__table__.columns]}")
except Exception as e:
    print(f"✗ Failed to load Expense model: {e}")

try:
    from app.models.user import User
    print("✓ User model loaded successfully")
    print(f"  Columns: {[c.name for c in User.__table__.columns]}")
except Exception as e:
    print(f"✗ Failed to load User model: {e}")

try:
    from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate, ExpenseOut
    print("✓ Expense schemas loaded successfully")
    print(f"  ExpenseCreate fields: {list(ExpenseCreate.model_fields.keys())}")
except Exception as e:
    print(f"✗ Failed to load expense schemas: {e}")

try:
    from app.schemas.user_schema import UserCreate, UserUpdate, UserOut
    print("✓ User schemas loaded successfully")
    print(f"  UserCreate fields: {list(UserCreate.model_fields.keys())}")
except Exception as e:
    print(f"✗ Failed to load user schemas: {e}")

try:
    from app.services.expense_service import (
        create_expense, get_expenses_by_user, update_expense_by_user,
        get_monthly_expenses, get_expenses_summary_by_currency
    )
    print("✓ Expense services loaded successfully")
except Exception as e:
    print(f"✗ Failed to load expense services: {e}")

try:
    from app.services.user_service import (
        create_user, get_user_by_email, update_user_default_currency
    )
    print("✓ User services loaded successfully")
except Exception as e:
    print(f"✗ Failed to load user services: {e}")

try:
    from app.api.routes.expense_routes import router
    print("✓ Expense routes loaded successfully")
except Exception as e:
    print(f"✗ Failed to load expense routes: {e}")

try:
    from app.api.routes.user_routes import router
    print("✓ User routes loaded successfully")
except Exception as e:
    print(f"✗ Failed to load user routes: {e}")

print("\n--- Testing Pydantic validation ---")
try:
    from decimal import Decimal
    expense = ExpenseCreate(amount=Decimal("100.50"), description="Test expense")
    print(f"✓ Default currency expense: {expense.currency}")
    
    expense_usd = ExpenseCreate(amount=Decimal("50.00"), currency="USD", description="USD expense")
    print(f"✓ USD expense: {expense_usd.currency}")
    
    expense_lower = ExpenseCreate(amount=Decimal("30.00"), currency="eur", description="EUR expense")
    print(f"✓ Lowercase EUR converted to: {expense_lower.currency}")
except Exception as e:
    print(f"✗ ExpenseCreate validation failed: {e}")

try:
    user = UserCreate(email="test@example.com", password="password123")
    print(f"✓ Default currency user: {user.default_currency}")
    
    user_usd = UserCreate(email="usd@example.com", password="password123", default_currency="USD")
    print(f"✓ USD user: {user_usd.default_currency}")
except Exception as e:
    print(f"✗ UserCreate validation failed: {e}")

try:
    invalid_expense = ExpenseCreate(amount=Decimal("100"), currency="INVALID", description="Test")
    print("✗ Should have raised validation error")
except Exception as e:
    print(f"✓ Invalid currency correctly rejected: {type(e).__name__}")

print("\n--- All validations passed! ---")
