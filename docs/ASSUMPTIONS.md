# ASSUMPTIONS.md — Asistente de Reestructuración Financiera

Este documento lista los **supuestos**, **decisiones** y **límites** asumidos para implementar la solución.

---

## 1) Supuestos de ejecución (runtime)

- La aplicación corre como **una sola web app**: FastAPI sirve **API + UI** en el mismo host/puerto.
- En modo local, el comando `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` es suficiente para levantar todo.
- En Azure App Service, la app corre en **Linux (Python)** y se expone por `0.0.0.0:8000` (o el puerto indicado por la plataforma).

---

## 2) Supuestos de datos (datasets)

- Todos los datasets contienen una clave común `customer_id` (o equivalente) que permite **consolidar por cliente**.
- Los CSV vienen con **encabezados** (header) y separador estándar (coma), o son parseables por el lector usado en el backend.
- Los montos/valores numéricos son consistentes (por ejemplo, sin mezclar moneda/escala dentro de la misma columna).
- El dataset de `bank_offers.json` representa ofertas para consolidación y se asume como:
  - Un **JSON válido**.
  - Preferiblemente un **array/lista de objetos** (cada objeto = una oferta).

Ejemplo (estructura esperada):
```json
    [
      {
        "offer_id": "OF-CONSO-24M",
        "product_types_eligible": ["card", "personal"],
        "max_consolidated_balance": 50000,
        "new_rate_pct": 19.9,
        "max_term_months": 24,
        "conditions": "..."
      }
    ]
```

> Nota: si `bank_offers.json` no es una lista de objetos, la consolidación puede omitirse o fallar dependiendo de la validación aplicada.

---

## 3) Supuestos funcionales (escenarios)

- Se calculan **al menos 3 escenarios** por cliente:
  - `minimum_payment`: referencia/base.
  - `optimized_plan`: prioriza deudas con mayor tasa/mora (y/o estrategia definida en la lógica).
  - `consolidation`: solo si existen ofertas aplicables según `bank_offers`.

- Métricas comparables entre escenarios:
  - `total_months`
  - `total_interest_paid`
  - `interest_savings_vs_minimum`
  - `months_saved_vs_minimum`

- La **consolidación** se considera “aplicable” si hay al menos una oferta válida que cubra el tipo de producto y el monto (según reglas del modelo).

---

## 4) Supuestos de UI (carga opcional)

- La UI permite subir archivos, pero la **subida es opcional**:
  - Si el usuario no sube nada, la app usa los datasets precargados desde `./data`.
  - Si se suben archivos, estos **reemplazan la data en memoria**.

- La UI identifica los archivos por “convención de nombre”:
  - Revisa si el filename (lowercase) contiene: `loans`, `cards`, `payments_history`, `credit_score_history`, `customer_cashflow`, `bank_offers`.

> Nota: esto es una decisión de UX para simplificar el upload sin un mapeo manual por campo.

---

## 5) Supuestos de IA (Azure OpenAI / Foundry)

- El informe se genera usando Azure OpenAI (Foundry) mediante variables:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_DEPLOYMENT`
  - `AZURE_OPENAI_API_VERSION`

- Se asume que el deployment existe y tiene permisos para responder.
- Si la IA falla por configuración/timeout/cuota, el comportamiento esperado es:
  - retornar error controlado, o
  - retornar un texto alternativo.

---

## 6) Persistencia y reinicios

- `POST /datasets/upload` **NO guarda archivos en disco**.
- Los datasets subidos viven en memoria:
  - al reiniciar el proceso, se pierde esa data y se recarga desde `./data`.

---

## 7) Seguridad y autenticación (alcance del demo)

- No se implementa autenticación/autorización (demo).
- No se asume uso en producción multi-tenant ni exposición pública sin controles adicionales.

---

## 8) Límites / fuera de alcance

- No se implementa:
  - Gestión avanzada de usuarios / roles.
  - Persistencia de uploads en almacenamiento (Blob, File Share, etc.).
  - Observabilidad completa (APM, tracing distribuido).
  - Reglas bancarias reales (scoring/reglas regulatorias).
  - Validaciones exhaustivas de calidad de datos (más allá de lo mínimo necesario para el demo).

---

## 9) Decisiones de implementación

- **Monolito liviano** (FastAPI + UI estática) para que el evaluador pruebe rápido sin desplegar 2 servicios.
- **Modo demo out-of-the-box** para evitar dependencia de upload.
- **Upload en memoria** para simplificar y cumplir el reto (y evitar persistencia/archivos).
- **Documentación separada** (`README.md` + `docs/`) para que sea fácil evaluar: arquitectura, API y supuestos.
