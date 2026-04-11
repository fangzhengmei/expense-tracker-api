# expense-tracker-api

### 🔐 Auth
---
* POST /auth/register → Crear usuario
* POST /auth/login → Login (devuelve JWT)
* GET /auth/me → Obtener usuario autenticado


### 💸 Expenses
---
* POST /expenses → Crear gasto
* GET /expenses → Listar gastos (con filtros opcionales: fecha, categoría)
* GET /expenses/{id} → Obtener un gasto concreto
* PUT /expenses/{id} → Actualizar gasto
* DELETE /expenses/{id} → Eliminar gasto

### 📊 Analytics
---
* GET /analytics/monthly → Resumen mensual (total, media, etc.)
* GET /analytics/categories → Gastos por categoría


### 🏷️ Categories (esto suele faltar en juniors, pero en la vida real siempre está)
---
* POST /categories → Crear categoría
* GET /categories → Listar categorías
* PUT /categories/{id} → Actualizar categoría
* DELETE /categories/{id} → Eliminar categoría


### ⚙️ Notas de alguien que ha visto muchos proyectos junior
---
* Prefijo /auth → bien, separa responsabilidades
* Añadir /me → da puntos, demuestra que entiendes JWT
* CRUD completo en expenses → obligatorio
* Categories separadas → esto te sube de nivel directamente
* Analytics → bien, pero no lo sobrecomplices al principio




expense-tracker-api/
 │
 ├── app/
 │       ├── __init__.py 
 │       ├── main.py 
 │       │ 
 │       ├── api/ 
 │       │        ├── __init__.py 
 │       │        ├── deps.py 
 │       │        └── routes/ 
 │       │                  ├── __init__.py 
 │       │                  ├── expense_routes.py 
 │       │                  └── user_routes.py 
 │       │ 
 │       ├── core/ 
 │       │       ├── __init__.py 
 │       │       ├── config.py 
 │       │       ├── jwt.py 
 │       │       └── security.py 
 │       │ 
 │       ├── db/ 
 │       │       ├── __init__.py 
 │       │       └── database.py 
 │       │ 
 │       ├── models/ 
 │       │        ├── __init__.py 
 │       │        ├── expense.py 
 │       │        └── user.py 
 │       │ 
 │       ├── schemas/ 
 │       │        ├── __init__.py 
 │       │        ├── expense_schema.py 
 │       │        └── user_schema.py 
 │       │ 
 │       └── services/ 
 │                 ├── __init__.py 
 │                 ├── expense_service.py 
 │                 └── user_service.py 
 │
 ├── tests/
 │       ├── __init__.py
 │       ├── conftest.py
 │       ├── test_auth.py
 │       ├── test_expenses.py
 │       └── utils.py
 │
 ├── .venv
 ├── ENDPOINTS.md
 ├── README.md
 └── requirements.txt