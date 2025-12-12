# Arquitectura

Este documento describe la arquitectura y el flujo de la solución **Asistente de Reestructuración Financiera**.

## Resumen

La aplicación es una **web app en FastAPI** que:

- Carga datasets (por defecto desde `./data/`) al iniciar.
- Expone endpoints para listar clientes, calcular escenarios y generar reporte.
- Sirve una **UI estática** (HTML/CSS/JS) desde el mismo FastAPI en `/`, por lo que **frontend y backend corren en el mismo host/puerto**.
- (Opcional) Permite subir datasets vía `POST /datasets/upload` para reemplazar la data **en memoria** sin persistir en disco.
- Genera un informe en lenguaje natural usando **Azure OpenAI (AI Foundry / Azure OpenAI)**.

---

## Componentes principales

## Estructura del proyecto (carpetas)

El repo está organizado así (resumen):

- `app/`
  - `main.py`: punto de entrada de FastAPI.
  - `static/`: UI web (HTML/CSS/JS) servida por FastAPI.
  - `models/`: modelos/DTOs usados en requests/responses y parsing.
  - `services/`: lógica de negocio (cálculo de escenarios, consolidación, generación de reporte).
  - `utils/`: utilidades compartidas.
- `data/`: datasets por defecto para modo demo (carga automática al iniciar).
- `docs/`: documentación del proyecto (architecture, api, decisions, etc.).
- `requirements.txt`: dependencias Python.
- `README.md`: guía rápida para correr local y demo en Azure.

### 1) API (FastAPI)
Responsable de:
- Exponer endpoints HTTP.
- Orquestar el flujo: consolidación → simulación → respuesta.
- Servir la UI estática como `StaticFiles`.

### 2) UI (HTML/CSS/JS)
Responsable de:
- Permitir (opcionalmente) subir datasets.
- Listar clientes desde `GET /customers`.
- Consultar overview de escenarios y mostrarlo en tabla.
- Solicitar la generación del reporte por cliente.

> La UI consume la API por rutas relativas (mismo dominio/puerto). Por eso en producción y local se comporta igual.

### 3) Capa de datos en memoria (App State)
- En startup se carga `./data/` y se mantiene un objeto en memoria (por ejemplo `app.state.data`).
- Cuando se usa `POST /datasets/upload`, se parsean los archivos subidos y se **reemplaza** la data en memoria.

**Importante:** al reiniciar el proceso (local o App Service), se pierde la memoria y se vuelve a cargar `./data/`.

### 4) Motor de escenarios
Responsable de simular 3 escenarios por cliente:
- `minimum_payment`
- `optimized_plan`
- `consolidation` (si aplica)

El resultado estándar incluye métricas como:
- `total_months`
- `total_interest_paid`
- `interest_savings_vs_minimum`
- `months_saved_vs_minimum`

### 5) Generación de informe (LLM)
- Se construye un prompt con el resumen del cliente + resultados de escenarios.
- Se llama a Azure OpenAI con variables de entorno.
- Se devuelve `report_text` listo para mostrar en la UI o consumir por API.

---

## Flujo end-to-end

### Flujo A (sin subir datasets: demo out-of-the-box)
1. El usuario inicia la app (`uvicorn app.main:app ...`).
2. En startup, la app carga datasets desde `./data/`.
3. La UI abre `/` y ejecuta `GET /customers`.
4. El usuario selecciona un cliente.
5. La UI llama `GET /customers/{id}/scenarios/overview`.
6. La UI llama `GET /customers/{id}/report` para generar el informe con IA.

### Flujo B (subiendo datasets por UI/API)
1. El usuario inicia la app.
2. En la UI (sección “Carga de datasets”) selecciona 6 archivos.
3. La UI valida nombres y llama `POST /datasets/upload` con `multipart/form-data`.
4. El backend parsea archivos y reemplaza data en memoria.
5. La UI refresca clientes (`GET /customers`) y se usa el mismo flujo de escenarios y reporte.

---

## Formatos y reglas

### Identificación de archivos en UI (upload)
La UI construye un `fileMap` buscando que el nombre del archivo (en minúsculas) contenga estas claves:

- `loans`
- `cards`
- `payments_history`
- `credit_score_history`
- `customer_cashflow`
- `bank_offers`

Si falta alguno, no envía el POST y marca faltantes.

### Persistencia
- No se persisten uploads a disco (por diseño).
- `./data/` funciona como dataset base de demo.
- En App Service, la memoria no es persistente entre reinicios.

---

## Consideraciones de despliegue

### Un solo proceso (API + UI)
La UI es estática y es servida por FastAPI, por lo que el despliegue es un único servicio.

- Local:
  - `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

- Azure App Service (recomendado):
  - `gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000`

---

## Seguridad

- Las credenciales de Azure OpenAI **no se versionan** en GitHub.
- Se inyectan por variables de entorno (local `.env` / Azure Portal Configuration).
- El upload no escribe archivos a disco (evita dejar datasets subidos como artefactos del servidor).

---

## Limitaciones conocidas

- El upload reemplaza data en memoria; si el servicio reinicia, vuelve a `./data/`.
- La consolidación depende de la estructura de `bank_offers.json` (lista de objetos).
- Si faltan campos críticos en datasets, algunos escenarios pueden omitirse o devolver error validado.

---

## Diagrama rápido (texto)

Usuario
→ UI (/)
→ API FastAPI
→ Data en memoria (startup: ./data)
→ Motor de escenarios (minimum / optimized / consolidation)
→ LLM (Azure OpenAI / AI Foundry)
→ Respuesta (overview / report_text)
