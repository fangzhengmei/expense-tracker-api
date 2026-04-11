# 🧪 Tests --- Expense Tracker API

## 📌 Objetivo

Esta carpeta contiene la suite de tests del proyecto.\
El objetivo es validar:

-   Autenticación (registro y login)
-   CRUD de gastos
-   Seguridad por usuario (aislamiento)
-   Endpoint de analytics

------------------------------------------------------------------------

## 🧱 Estructura

-   `conftest.py` → configuración global de tests (DB y cliente)
-   `test_auth.py` → tests de autenticación
-   `test_expenses.py` → tests de gastos
-   `utils.py` → funciones auxiliares reutilizables

------------------------------------------------------------------------

## ⚙️ Cómo funcionan

### Base de datos aislada

Cada test usa una base de datos SQLite independiente.

``` python
Base.metadata.drop_all()
Base.metadata.create_all()
```

👉 Esto garantiza que los tests no interfieren entre sí.

------------------------------------------------------------------------

### Cliente de testing

Se usa `TestClient` de FastAPI para simular peticiones HTTP reales.

------------------------------------------------------------------------

### Override de dependencias

Se reemplaza `get_db` para usar la base de datos de test:

``` python
app.dependency_overrides[get_db] = override_get_db
```

------------------------------------------------------------------------

## 🔐 Tests de autenticación

Cubren:

-   Registro correcto
-   Login correcto
-   Login incorrecto
-   Registro duplicado

------------------------------------------------------------------------

## 💸 Tests de gastos

Cubren:

-   Crear gasto
-   Listar gastos
-   Actualizar gasto
-   Eliminar gasto
-   Seguridad (no acceso a recursos de otro usuario)
-   Analytics mensual

------------------------------------------------------------------------

## 🧠 Decisiones importantes

### 404 vs 403

Se devuelve `404` cuando un usuario intenta acceder a un recurso que no
le pertenece.

👉 Esto evita revelar la existencia de recursos de otros usuarios.

------------------------------------------------------------------------

### Uso de utils

Funciones como:

-   `create_user_and_login`
-   `create_expense`

👉 Evitan duplicación y hacen los tests más claros.

------------------------------------------------------------------------

## ▶️ Ejecutar tests

``` bash
pytest -v
```

------------------------------------------------------------------------

## 🎯 Resultado

Tests:

-   Aislados
-   Reproducibles
-   Representan comportamiento real de la API
