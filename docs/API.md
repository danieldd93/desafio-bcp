# API.md — Asistente de Reestructuración Financiera

Este documento describe los endpoints expuestos por la API (FastAPI) y cómo consumirlos desde scripts o desde la UI.

> La aplicación sirve **UI + API en el mismo host/puerto** cuando se ejecuta `uvicorn app.main:app ...`.

---

## Base URL

- Local: `http://127.0.0.1:8000`
- Azure (demo): `https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net`

---

## Autenticación

No requiere autenticación (demo).

---

## Content-Types

- Endpoints JSON: `application/json`
- Upload de datasets: `multipart/form-data`

---

## Health / UI

### `GET /`
Devuelve la **UI web** (HTML) si está habilitada/servida por el backend.

**Respuesta:** HTML (`text/html`)

---

## Datasets

### `POST /datasets/upload`
Sube datasets para **reemplazar** la data cargada en memoria (5 CSV + 1 JSON).

- **Content-Type:** `multipart/form-data`
- **Fields requeridos:**
  - `loans` (CSV)
  - `cards` (CSV)
  - `payments_history` (CSV)
  - `credit_score_history` (CSV)
  - `customer_cashflow` (CSV)
  - `bank_offers` (JSON)

> Importante: este endpoint **no guarda archivos en disco**; procesa y mantiene la data **en memoria**.

#### Respuesta (ejemplo)
```json
{
  "status": "ok",
  "message": "Datasets cargados y reemplazados correctamente.",
  "rows_per_dataset": {
    "loans": 100,
    "cards": 200,
    "payments_history": 800,
    "credit_score_history": 24,
    "customer_cashflow": 12,
    "bank_offers": 10
  }
}
```

#### cURL (ejemplo)
    curl -X POST "http://127.0.0.1:8000/datasets/upload" \
      -F "loans=@./data/loans.csv;type=text/csv" \
      -F "cards=@./data/cards.csv;type=text/csv" \
      -F "payments_history=@./data/payments_history.csv;type=text/csv" \
      -F "credit_score_history=@./data/credit_score_history.csv;type=text/csv" \
      -F "customer_cashflow=@./data/customer_cashflow.csv;type=text/csv" \
      -F "bank_offers=@./data/bank_offers.json;type=application/json"

---

## Clientes

### `GET /customers`
Devuelve lista de `customer_id` disponibles según la data cargada (desde `./data` al arranque o desde `POST /datasets/upload`).

#### Respuesta (ejemplo)
    ["CU-001", "CU-002", "CU-003"]

---

## Escenarios

### `GET /customers/{customer_id}/scenarios/overview`
Devuelve el resumen comparativo de escenarios del cliente:

- `minimum_payment` (pago mínimo)
- `optimized_plan` (plan optimizado)
- `consolidation` (consolidación, **si aplica** según `bank_offers`)

#### Respuesta (ejemplo simplificado)
    {
      "customer_id": "CU-001",
      "scenarios": [
        {
          "scenario_type": "minimum_payment",
          "total_months": 266,
          "total_interest_paid": 19055.5,
          "interest_savings_vs_minimum": 0.0,
          "months_saved_vs_minimum": 0
        },
        {
          "scenario_type": "optimized_plan",
          "total_months": 16,
          "total_interest_paid": 4545.53,
          "interest_savings_vs_minimum": 14509.97,
          "months_saved_vs_minimum": 250
        },
        {
          "scenario_type": "consolidation",
          "total_months": 24,
          "total_interest_paid": 4737.03,
          "interest_savings_vs_minimum": 14318.47,
          "months_saved_vs_minimum": 242
        }
      ]
    }

#### Errores comunes
- `404` si el `customer_id` no existe en la data cargada.
- `422` si el path param no cumple validación (según implementación).

---

## Reporte IA

### `GET /customers/{customer_id}/report`
Genera y devuelve el informe explicativo usando Azure OpenAI (Foundry) y la data consolidada del cliente.

#### Respuesta (ejemplo)
    {
      "customer_id": "CU-001",
      "language": "es",
      "report_text": "..."
    }

#### Notas
- Si las variables de entorno de Azure OpenAI no están configuradas, este endpoint puede:
  - fallar (5xx/4xx según implementación), o
  - devolver un texto alternativo (si existe fallback).

---

## Variables de entorno (Azure OpenAI / Foundry)

Crea un archivo `.env` (NO se sube a GitHub) o exporta variables:

    AZURE_OPENAI_ENDPOINT=https://<tu-recurso>.cognitiveservices.azure.com/
    AZURE_OPENAI_API_KEY=<tu_api_key>
    AZURE_OPENAI_DEPLOYMENT=<tu_deployment_name>
    AZURE_OPENAI_API_VERSION=2025-03-01-preview

---

## Flujo recomendado de uso

### Opción A — Demo out-of-the-box (sin upload)
1. Inicia la app (carga `./data` automáticamente).
2. `GET /customers`
3. `GET /customers/{id}/scenarios/overview`
4. `GET /customers/{id}/report`

### Opción B — Con tus archivos (upload opcional)
1. `POST /datasets/upload` con los 6 archivos.
2. Repite los endpoints de clientes, overview y report.

---

## Troubleshooting

### 1) Upload falla por `python-multipart`
Si ves error tipo:
- `Form data requires "python-multipart" to be installed`

Solución:
    pip install python-multipart

### 2) Reporte IA falla por api-version
Si ves:
- `Responses API is enabled only for api-version 2025-03-01-preview and later`

Solución:
- `AZURE_OPENAI_API_VERSION=2025-03-01-preview`

### 3) 404 en `/customers` desde la UI
Causa típica:
- Estás abriendo la UI desde un host distinto al de la API (o `BASE_URL` apunta mal).

Solución:
- Abrir la UI desde el mismo servidor que corre FastAPI (`http://127.0.0.1:8000/`) o ajustar `BASE_URL` si tu UI está en otro origen.

---
