# Asistente de Reestructuración Financiera

Web app (FastAPI) que **procesa datasets por cliente**, **simula escenarios de pago de deuda** (pago mínimo, plan optimizado y consolidación si aplica), **calcula ahorro estimado** y **genera un informe explicativo en lenguaje natural** usando Azure OpenAI.

---

## Requerimientos del reto cubiertos

- [x] Procesa archivos entregados y consolida la información por cliente.
- [x] Genera al menos 3 escenarios por cliente:
  - **Pago mínimo**
  - **Plan optimizado** (prioriza mayor tasa y mora, ajustado a flujo de caja)
  - **Consolidación (si aplica)** usando `bank_offers.json`
- [x] Calcula el **ahorro estimado** por escenario (vs pago mínimo).
- [x] Genera **informe explicativo** en lenguaje natural por cliente (IA generativa).
- [x] Implementado en **Python** (FastAPI).
- [x] (Opcional) **Despliegue en Azure App Service** con demo web.

---

## Arquitectura / flujo (alto nivel)

1. **Carga inicial (startup):** la app carga datasets desde `./data/` (modo demo out-of-the-box).
2. **Carga por UI / API (opcional):** `POST /datasets/upload` permite subir CSV/JSON y **reemplaza los datasets en memoria**.
3. **Consolidación por cliente:** se agrupa información por `customer_id`.
4. **Cálculo de escenarios:** se simulan escenarios y se calculan métricas (meses, intereses, ahorro vs mínimo).
5. **Reporte IA:** se construye un prompt con el resumen y se llama a Azure OpenAI.
6. **Respuesta:** la API devuelve JSON con overview y/o `report_text` para el cliente.

> Nota: el endpoint de upload **no guarda archivos en disco**; el procesamiento ocurre en memoria.

---

## Endpoints (API)

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

**Respuesta (ejemplo):**
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

---

### `GET /customers`
Devuelve lista de `customer_id` disponibles.

**Respuesta (ejemplo):**
```json
["CU-001", "CU-002", "CU-003"]
```

---

### `GET /customers/{customer_id}/scenarios/overview`
Devuelve el resumen comparativo de escenarios del cliente (meses, intereses, ahorro vs mínimo, etc.).

**Respuesta (ejemplo simplificado):**
```json
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
```

---

### `GET /customers/{customer_id}/report`
Genera y devuelve el informe explicativo con IA.

**Respuesta (ejemplo):**
```json
{
  "customer_id": "CU-001",
  "language": "es",
  "report_text": "..."
}
```

## Formato de entrada (datasets)

### Archivos requeridos
- `loans.csv`
- `cards.csv`
- `payments_history.csv`
- `credit_score_history.csv`
- `customer_cashflow.csv`
- `bank_offers.json`

### Convención de nombres (para la UI)
La UI mapea archivos por nombre: busca que el **filename contenga** estas claves:

- `loans`
- `cards`
- `payments_history`
- `credit_score_history`
- `customer_cashflow`
- `bank_offers`

Ejemplos válidos:
- `loans.csv`
- `cards_2025.csv`
- `payments_history_v2.csv`
- `credit_score_history.csv`
- `customer_cashflow.csv`
- `bank_offers.json`

### Nota especial: `bank_offers.json`
- Debe ser un **JSON válido** (no CSV).
- Recomendado: que sea una **lista (array) de objetos** con los campos esperados por el modelo `BankOffer` (cada elemento representa una oferta).

Ejemplo (estructura general):
```json
[
  {
    "offer_id": "OF-CONSO-24M",
    "product_types_eligible": ["card", "personal"],
    "max_consolidated_balance": 50000,
    "new_rate_pct": 19.9,
    "max_term_months": 24,
    "conditions": "No mora >30 días al momento de la solicitud"
  },
  {
    "offer_id": "OF-CONSO-36M",
    "product_types_eligible": ["card", "personal", "micro"],
    "max_consolidated_balance": 75000,
    "new_rate_pct": 17.5,
    "max_term_months": 36,
    "conditions": "Score > 650 y sin mora activa"
  }
]
```

> Si el JSON no viene como lista de objetos (por ejemplo, viene como strings o anidado), la simulación de consolidación puede fallar al parsear (`BankOffer(**o)` requiere que `o` sea un objeto/dict).

## Cómo correr local

### 1) Requisitos
- Python 3.11+ (recomendado)
- pip
- (Opcional) Git

### 2) Crear entorno e instalar dependencias
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

> Si usas el endpoint de upload con `multipart/form-data`, asegúrate de tener:
```bash
pip install python-multipart
```

### 3) Variables de entorno (Azure OpenAI)
Crea un archivo `.env` (local) o exporta variables en tu terminal:

```bash
export AZURE_OPENAI_ENDPOINT="https://<tu-recurso>.cognitiveservices.azure.com/"
export AZURE_OPENAI_API_KEY="<tu_api_key>"
export AZURE_OPENAI_DEPLOYMENT="gpt-5-mini-desafio"
export AZURE_OPENAI_API_VERSION="2025-03-01-preview"
```

### 4) Ejecutar la app
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir en navegador:
- UI / Home: `http://127.0.0.1:8000/`

### 5) Flujo de uso (local)
Opción A (demo out-of-the-box):
1. Inicia la app.
2. Usa `GET /customers` para listar clientes (data cargada desde `/data` al arranque).

Opción B (subir datasets por UI / API):
1. En la UI, sube los 6 archivos (5 CSV + 1 JSON `bank_offers`).
2. Click **“Subir y procesar”** (POST `/datasets/upload`).
3. Luego: **“Ver resumen”** y **“Generar informe”** por cliente.

## Despliegue en Azure App Service (opcional)

Este repo puede desplegarse como **Web App Linux (Python)** en Azure App Service.

### App Settings necesarios (Azure Portal → Configuration)
Configura estas variables de entorno:

- `AZURE_OPENAI_ENDPOINT` = `https://<tu-recurso>.cognitiveservices.azure.com/`
- `AZURE_OPENAI_API_KEY` = `<tu_key>`
- `AZURE_OPENAI_DEPLOYMENT` = `<tu_deployment>`
- `AZURE_OPENAI_API_VERSION` = `2025-03-01-preview`

Recomendadas para App Service:
- `SCM_DO_BUILD_DURING_DEPLOYMENT` = `1` (para que instale requirements al desplegar)
- `WEBSITES_PORT` = `8000` (si tu comando escucha en 8000)

### Startup Command (muy importante)
En Azure Portal → Configuration → General settings → **Startup Command**:

- Opción A (Gunicorn + UvicornWorker):
  - `gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000`

> Si el sitio “no levanta en 10 mins”, 8 de cada 10 veces es por Startup Command / puerto / dependencias.

### Deploy (Zip Deploy)
Desde tu máquina (Azure CLI):

1) Crear el zip (incluye `app/`, `data/`, `requirements.txt`, etc.)
2) Desplegar:
- `az webapp deploy --resource-group <RG> --name <APP_NAME> --type zip --src-path deploy.zip`

### Redeploy (re-despliegue)
Solo repite el deploy del zip (con el zip actualizado):

- `az webapp deploy --resource-group <RG> --name <APP_NAME> --type zip --src-path deploy.zip`

Si te sale “Another deployment is in progress”, espera a que termine el anterior y reintenta.  
Si Kudu falla por conexión, suele ser temporal; un redeploy después normalmente entra.

---

## Nota sobre carga de datasets (memoria vs disco)

- En el arranque, la app carga datasets desde `./data/`:
  - Esto permite que el proyecto funcione “out-of-the-box” para demo/evaluación.

- Al usar `POST /datasets/upload`:
  - **No guarda archivos en `./data/`**
  - Lee los archivos subidos y reemplaza `app.state.data` **en memoria**
  - Es decir: la API empieza a trabajar con lo que subiste inmediatamente.
  - Si reinicias el App Service, volverá a cargar `./data/` (porque memoria se pierde).

---

## Supuestos y validaciones

- Si falta información crítica en algún dataset:
  - La API responde con error 400/422 según el caso.
- Consolidación:
  - Solo aplica si existen ofertas válidas para el cliente (según `bank_offers.json`).
  - Si `bank_offers` no tiene estructura válida, se omite consolidación o se devuelve un error controlado (según implementación).

### Estructura esperada de `bank_offers`
Para evitar errores tipo `BankOffer(**o) argument after ** must be a mapping`, la app espera que cada oferta sea un objeto (dict).

---

## Evidencia / demo

### Demo (Azure)
- URL: `https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net/`

### Generar informe para al menos 3 clientes
1) `GET /customers` → obtienes `CU-001`, `CU-002`, `CU-003` (ejemplo)
2) Para cada cliente:
   - `GET /customers/{id}/scenarios/overview`
   - `GET /customers/{id}/report`

Si usas la UI:
1) Seleccionas el cliente
2) “Ver resumen de escenarios”
3) “Generar informe”

---

## Notas / troubleshooting

### 1) Upload con FastAPI: falta `python-multipart`
Si ves:
- `Form data requires "python-multipart" to be installed`

Solución:
- Agregar `python-multipart` a `requirements.txt` e instalar.

### 2) Azure OpenAI + Responses API requiere api-version preview
Si ves:
- `Azure OpenAI Responses API is enabled only for api-version 2025-03-01-preview and later`

Solución:
- Setear `AZURE_OPENAI_API_VERSION=2025-03-01-preview`

### 3) Error 404 “Resource not found” en llamadas a OpenAI
Causas típicas:
- `AZURE_OPENAI_ENDPOINT` incorrecto (región/recurso equivocado)
- `AZURE_OPENAI_DEPLOYMENT` no existe o está mal escrito
- API version incorrecta
- Se está usando el cliente equivocado (recomendado usar `AzureOpenAI` cuando apuntas a Azure)

Checklist rápido:
- Endpoint = `https://<recurso>.cognitiveservices.azure.com/`
- Deployment = nombre exacto del deployment en Azure OpenAI
- Api version = `2025-03-01-preview`

### 4) App Service “failed to start within 10 mins”
Revisar:
- Startup Command (gunicorn/uvicorn)
- Puerto (usar `0.0.0.0:8000` + `WEBSITES_PORT=8000`)
- `SCM_DO_BUILD_DURING_DEPLOYMENT=1` para instalar dependencies

---
