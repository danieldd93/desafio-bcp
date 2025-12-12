# RUNBOOK.md — Asistente de Reestructuración Financiera

Este runbook describe cómo **levantar**, **probar**, **diagnosticar** y **recuperar** la aplicación en local y en Azure App Service.

---

## 1) Levantar en local

### 1.1 Preparación

- Tener Python 3.11+ (recomendado).
- Tener el repo clonado y ubicarse en la raíz del proyecto.

Activar entorno virtual e instalar dependencias:

    python -m venv venv
    source venv/bin/activate   # macOS/Linux
    # venv\Scripts\activate    # Windows

    pip install -r requirements.txt

Si usarás upload de datasets:

    pip install python-multipart

Variables de entorno (si vas a generar reporte con IA):

    export AZURE_OPENAI_ENDPOINT="https://<tu-recurso>.cognitiveservices.azure.com/"
    export AZURE_OPENAI_API_KEY="<tu_api_key>"
    export AZURE_OPENAI_DEPLOYMENT="<tu_deployment>"
    export AZURE_OPENAI_API_VERSION="2025-03-01-preview"

### 1.2 Arranque

Ejecuta:

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Verifica:
- UI: `http://127.0.0.1:8000/`
- API: `http://127.0.0.1:8000/customers`

Nota: este comando levanta **API + UI** (no hay que correr un servidor aparte para el frontend).

---

## 2) Flujo de prueba (smoke test)

### 2.1 Sin upload (modo demo)

1) Abre la UI y confirma que carga clientes.
2) Selecciona un cliente.
3) Click **“Ver resumen”**.
4) Click **“Generar informe”** (si IA está configurada).

Alternativa por API:
- GET `/customers`
- GET `/customers/{id}/scenarios/overview`
- GET `/customers/{id}/report`

### 2.2 Con upload (opcional)

1) En la UI, sube los 6 archivos (5 CSV + 1 JSON).
2) Click **“Subir y procesar”**.
3) Confirma que refresca lista de clientes.
4) Repite “Ver resumen” y “Generar informe”.

---

## 3) Problemas comunes (local) y solución

### 3.1 `uvicorn: command not found`

Causa típica:
- No estás dentro del `venv` donde se instaló uvicorn, o no está instalado.

Solución:

    source venv/bin/activate
    pip install -r requirements.txt

Y vuelve a ejecutar uvicorn.

### 3.2 Error: `Directory '<...>/static' does not exist`

Causa:
- El backend intenta montar `/static` apuntando a una carpeta que no existe.

Solución:
- Asegurar que exista la carpeta `static/` (o la ruta correcta), o que el backend use la ruta real donde está `index.html`.
- Verificar estructura esperada:
  - `static/index.html`

### 3.3 UI carga pero `/customers` da 404

Causa típica:
- Estás sirviendo el HTML con un servidor de archivos (por ejemplo `python -m http.server`) y NO con FastAPI.
- O el frontend está apuntando a un BASE_URL incorrecto.

Solución recomendada:
- Ejecutar solo con FastAPI:

      uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

- Confirmar que la UI hace `fetch("/customers")` (misma origin), sin necesidad de BASE_URL externo.

### 3.4 Upload falla con error de multipart

Error típico:
- `Form data requires "python-multipart" to be installed`

Solución:

    pip install python-multipart

Agregar `python-multipart` al `requirements.txt` si no está.

### 3.5 Reporte IA falla (Azure OpenAI)

Síntomas:
- 401/403, 404 resource not found, o error de api-version.

Checklist:
- Endpoint correcto: `https://<recurso>.cognitiveservices.azure.com/`
- Deployment existe y coincide el nombre exacto
- Api version: `2025-03-01-preview` (o la usada por tu implementación)
- Key válida y con permisos

---

## 4) Levantar en Azure App Service

### 4.1 Configuración mínima (Azure Portal → Configuration)

App settings:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`

Recomendadas:
- `SCM_DO_BUILD_DURING_DEPLOYMENT=1`
- `WEBSITES_PORT=8000`

### 4.2 Startup Command

Recomendado:

    gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000

---

## 5) Diagnóstico en Azure

### 5.1 Si “no levanta”

Revisar en este orden:
1) Startup Command (si está mal, la app no inicia).
2) Puerto (debe coincidir con `WEBSITES_PORT` y el bind).
3) Dependencias (que `requirements.txt` incluya uvicorn/gunicorn/fastapi).
4) Logs (Log stream) para ver el error exacto.

### 5.2 Si el sitio abre pero endpoints fallan

- Probar directamente:
  - `/customers`

Si `/customers` falla:
- Puede ser fallo de carga de datasets (`./data`) o error en startup.

---

## 6) Recuperación (rollback / redeploy)

### 6.1 Redeploy

- Rehacer zip deploy o pipeline (GitHub Actions si aplica).
- Si aparece “deployment in progress”, esperar y reintentar.

### 6.2 Volver a un commit anterior (GitHub)

- Opción simple:
  - Revertir el commit problemático y redeploy.

---

## 7) Operación diaria (qué mirar)

- Confirmar que `/` abre UI.
- Confirmar que `/customers` responde 200.
- Confirmar que `/customers/{id}/report` genera texto.
- Si se usó upload, recordar:
  - Los datos están en memoria; un reinicio vuelve a `./data`.

---

## 8) Nota rápida

Si funciona en local pero no en Azure: casi siempre es uno de estos 3:
- Startup Command
- Puerto
- App settings (variables de entorno)
