# Poner xFollow en marcha

## Requisitos

Node.js 22+, npm 10+, Python 3.10+ y un PostgreSQL accesible. Para Docker, necesitas Docker Compose y la red del PostgreSQL existente. La web utiliza una versión preliminar de Next.js fijada en el lockfile.

xFollow crea el esquema `xfollow`; su Compose contiene web, API y worker. La integración con las tablas de xTender y xReview es opcional. Las operaciones asistidas necesitan un modelo configurado.

## Preparar configuración y dependencias

```bash
cp .env.local.example .env.local
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r apps/api/requirements.txt
npm ci
```

Configura `POSTGRES_DSN` para acceso desde el host y `POSTGRES_DSN_DOCKER` para acceso desde contenedores. Configura `LLM_BASE_URL`, `LLM_MODEL` y, cuando proceda, `LLM_API_KEY`. El endpoint debe incluir `/v1` y el nombre del modelo debe coincidir con el que sirve tu proveedor. La plantilla contiene ejemplos, no una conexión preconfigurada a infraestructura real.

## Arranque con Docker

Si xTender se inició con `-p procureai`, su red será `procureai_default`; la plantilla apunta al contenedor PostgreSQL de ese proyecto. Con otra infraestructura, cambia `XFOLLOW_POSTGRES_NETWORK` y el hostname de `POSTGRES_DSN_DOCKER`.

```bash
docker compose --env-file .env.local up --build -d
```

Web: <http://localhost:3101>. API: <http://localhost:8101/docs>. La API aplica las migraciones y el worker procesa los trabajos persistentes de IA. Los archivos subidos se guardan en `data/evidence`, montado en API y worker. Configura almacenamiento S3 accesible cuando quieras descargar referencias heredadas de xReview.

## Desarrollo local

La API lee `.env.local`. En cada terminal, activa el entorno Python cuando corresponda y exporta las variables para que npm utilice los mismos puertos:

```bash
set -a
source .env.local
set +a
```

En una terminal:

```bash
PYTHONPATH=apps/api python -m xfollow_api.migrate
npm run api
```

En otras dos terminales:

```bash
npm run worker
```

```bash
npm run dev:web
```

Los puertos de la plantilla son 3101 y 8101. Sin exportar esas variables, los scripts históricos usan 3100 y 8100. Para pruebas aisladas puedes usar `XFOLLOW_FORCE_MEMORY=1`; no conserva datos entre procesos ni sustituye al worker persistente.

## Verificación y operación

```bash
npm test
npm run build
```

`/health` muestra el estado de las dependencias; `/integrations/status` informa sobre las tablas de integración disponibles. Si la base es obligatoria y no responde, el servicio informa del fallo. La web incorpora `NEXT_PUBLIC_XFOLLOW_API_BASE_URL` al compilar: reconstruye su imagen si cambias la URL pública.

Antes de exponer una instancia, configura autenticación bearer y un proxy de identidad confiable, TLS y credenciales propias. No publiques secretos en variables `NEXT_PUBLIC_*`. Consulta [SECURITY.md](../SECURITY.md).
