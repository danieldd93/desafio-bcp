# DEMO_STEPS.md — Asistente de Reestructuración Financiera

Este documento describe los pasos para demostrar la solución rápidamente (UI + API), tanto en la **demo de Azure** como en **local**.

---

## 1) Demo en Azure (recomendado para evaluadores)

### 1.1 Abrir la demo
1) Abrir en navegador:
   - `https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net/`

2) Confirmar que carga la UI (secciones: Carga de datasets, Selección de cliente, Comparación, Informe).

### 1.2 Flujo principal (sin subir archivos)
Este flujo usa datasets por defecto (cargados al iniciar desde `./data`).

1) En **“Selección de cliente”**, elegir un cliente del dropdown.
2) Click **“Ver resumen”** (Comparación de escenarios).
   - Ver tabla comparativa con:
     - Pago mínimo
     - Plan optimizado
     - Consolidación (si aplica)
3) Click **“Generar informe”**.
   - Ver texto generado en el panel de informe.

### 1.3 Evidencia por API (opcional)

Base URL:
- `https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net`

1) Listar clientes:

       curl -s https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net/customers

2) Overview de escenarios (reemplaza CU-001 por uno real devuelto en /customers):

       curl -s https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net/customers/CU-001/scenarios/overview

3) Reporte IA:

       curl -s https://desafio-bcp-app-ebb2hpbfawb4gxfq.canadacentral-01.azurewebsites.net/customers/CU-001/report

---

## 2) Demo en local

### 2.1 Levantar la app

1) Activar entorno:

       source venv/bin/activate

2) Ejecutar:

       uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

3) Abrir UI:
   - `http://127.0.0.1:8000/`

### 2.2 Flujo principal (sin subir archivos)

1) Verificar que el selector de cliente carga opciones.
2) Seleccionar un cliente.
3) Click **“Ver resumen”**.
4) Click **“Generar informe”**.
   - Nota: para que funcione IA necesitas variables de entorno de Azure OpenAI configuradas.

### 2.3 Evidencia por API (local)

1) Clientes:

       curl -s http://127.0.0.1:8000/customers

2) Overview:

       curl -s http://127.0.0.1:8000/customers/CU-001/scenarios/overview

3) Reporte:

       curl -s http://127.0.0.1:8000/customers/CU-001/report

---

## 3) Demo con upload de datasets (opcional)

Este flujo demuestra que la app puede reemplazar datasets en memoria mediante UI o API.

### 3.1 Reglas de nombres (UI)
La UI identifica archivos según si el nombre contiene estas claves:
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

### 3.2 Upload por UI
1) En **“(Opcional) Carga de datasets”**, seleccionar los 6 archivos.
2) Click **“Subir y procesar”**.
3) Confirmar mensaje de éxito y recarga de clientes.
4) Seleccionar cliente y ejecutar:
   - “Ver resumen”
   - “Generar informe”

### 3.3 Upload por API (alternativa)

Ejemplo (ajusta rutas a tus archivos):

       curl -X POST http://127.0.0.1:8000/datasets/upload \
         -F "loans=@./data/loans.csv" \
         -F "cards=@./data/cards.csv" \
         -F "payments_history=@./data/payments_history.csv" \
         -F "credit_score_history=@./data/credit_score_history.csv" \
         -F "customer_cashflow=@./data/customer_cashflow.csv" \
         -F "bank_offers=@./data/bank_offers.json"

Luego repetir:

       curl -s http://127.0.0.1:8000/customers

---

## 4) Qué mostrar (checklist para evaluación)

- UI funcionando en `/` (misma app sirve frontend y backend).
- `/customers` retorna lista.
- Overview muestra 3 escenarios (mínimo, optimizado, consolidación si aplica).
- Reporte IA genera explicación en lenguaje natural.
- Upload opcional (si se quiere demostrar reemplazo en memoria).

---

## 5) Nota importante (memoria vs reinicio)

- Upload reemplaza datasets **en memoria**.
- Si la app se reinicia (local o Azure), vuelve a cargar los datasets por defecto desde `./data`.
