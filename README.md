# 💸 Expense Tracker API

API backend para la gestión de gastos personales con autenticación JWT,
arquitectura limpia y tests aislados.

------------------------------------------------------------------------

## 🎯 Objetivo

Construir una API realista que demuestre:

-   Autenticación segura
-   Gestión de datos por usuario
-   Arquitectura escalable
-   Testing fiable

------------------------------------------------------------------------

## 🧱 Stack

-   FastAPI
-   PostgreSQL
-   SQLAlchemy
-   Pydantic v2
-   Passlib (bcrypt)
-   python-jose (JWT)
-   Pytest

------------------------------------------------------------------------

## 📁 Estructura

    app/
     ├── api/        # Rutas y dependencias
     ├── core/       # Configuración y seguridad
     ├── db/         # Conexión a base de datos
     ├── models/     # Modelos SQLAlchemy
     ├── schemas/    # Validación (Pydantic)
     └── services/   # Lógica de negocio

    tests/           # Suite de tests

------------------------------------------------------------------------

## 🔐 Autenticación

Flujo:

1.  Register → crea usuario
2.  Login → devuelve JWT
3.  Requests protegidas → requieren token

------------------------------------------------------------------------

## 💸 Endpoints principales

### Auth

-   `POST /users/register`
-   `POST /users/login`
-   `GET /users/me`

### Expenses

-   `POST /expenses`
-   `GET /expenses`
-   `PUT /expenses/{id}`
-   `DELETE /expenses/{id}`

### Analytics

-   `GET /expenses/analytics/monthly`

------------------------------------------------------------------------

## 🧠 Decisiones técnicas

### ✔ Uso de Decimal

Se utiliza `Decimal` en lugar de `float` para evitar errores de
precisión en valores monetarios.

------------------------------------------------------------------------

### ✔ Seguridad por diseño

Se devuelve `404` en lugar de `403` cuando un usuario accede a recursos
ajenos.

👉 Evita revelar la existencia de datos de otros usuarios.

------------------------------------------------------------------------

### ✔ Arquitectura desacoplada

-   **routes** → capa HTTP
-   **services** → lógica de negocio
-   **models** → persistencia

👉 Facilita testing y mantenimiento.

------------------------------------------------------------------------

## 🧪 Testing

-   Base de datos aislada por test
-   Override de dependencias
-   Cobertura de auth, CRUD y seguridad

Ejecutar tests:

``` bash
pytest -v
```

------------------------------------------------------------------------

## ▶️ Ejecutar proyecto

``` bash
uvicorn app.main:app --reload
```

------------------------------------------------------------------------

## 🎯 Estado

✔ Listo para portfolio\
✔ Listo para entrevistas backend junior\
✔ Código limpio, probado y estructurado
# expense-tracker-api
# expense-tracker-api
