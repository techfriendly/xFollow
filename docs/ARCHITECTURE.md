# Arquitectura de xFollow

## Limites

xFollow cubre la fase de ejecución contractual. No valora ofertas ni prepara pliegos. Puede importar el expediente de xTender o el paquete inmutable de un lote adjudicado en xreview, pero no reescribe sus datos de origen.

## Componentes

| Componente | Responsabilidad |
| --- | --- |
| `apps/web` | Interfaz Next.js para contratos, obligaciones, alertas, tareas, cumplimiento, proteccion de datos, facturas, cambios contractuales, documentos, penalidades y expedientes. |
| `apps/api` | API FastAPI, reglas de negocio, importadores, cálculos, liquidación, auditoría, cliente `llm2` y persistencia. |
| `apps/api/xfollow_api/worker.py` | Proceso independiente que reclama y ejecuta trabajos de IA persistidos. |
| PostgreSQL | Dependencia externa configurable mediante `POSTGRES_DSN`; xFollow crea solo el esquema `xfollow` y lee las tablas publicas de ProcureAI mediante adaptadores opcionales. |
| Almacenamiento | Evidencias guardadas por hash en `data/evidence` en local; preparado para sustituir por SeaweedFS S3 en despliegue. |
| LLM OpenAI-compatible | `llm2` para extraer obligaciones, verificar evidencias y redactar borradores; siempre como resultado revisable. |

## Sinergias con ProcureAI

- Reutiliza el PostgreSQL existente, el tenant y el contexto de usuario cuando estan disponibles.
- Importa expedientes desde `procurement_workspaces` si la tabla existe.
- Usa `kb_tenders` y `kb_chunks` como base de conocimiento de PCSP si las tablas existen.
- Lee `xreview.award_handoffs` para listar adjudicaciones publicadas del mismo tenant. La importación usa `source_kind=xreview`, es única por procedimiento/lote, enlaza los `object_key` de SeaweedFS y conserva los ids de procedimiento, lote y oferta.
- Mantiene el mismo criterio de asistencia IA: borrador, trazabilidad, validacion humana y archivo no destructivo.

La deteccion de estas relaciones se realiza al vuelo en `xfollow_api.integrations`. Una instalacion sin tablas de ProcureAI no falla: el nucleo conserva altas manuales, ficha, alertas, tareas, documentos y devolucion.

## Despliegue

```text
 navegador :3101  ->  xFollow web
                         |
                         v
                    xFollow API :8101
                      |       |                  xFollow worker
                      |       +------------+           |
                      |                    |           v
                      +--------------------+--> PostgreSQL / xfollow.ai_jobs
                      |       |
                      |       +--> llm2 OpenAI-compatible (/v1)
                      +----------> PostgreSQL existente
                                  +- esquema xfollow
                                  +- tablas publicas opcionales
```

`docker-compose.yml` no define PostgreSQL. La API ejecuta migraciones idempotentes con bloqueo transaccional y el proceso de arranque falla de forma visible si la base configurada no está disponible en un entorno que la exige. El worker usa `FOR UPDATE SKIP LOCKED` para reclamar un trabajo sin interferir con otra instancia, conserva el contexto congelado y reintenta los errores transitorios con espera exponencial limitada.

## Permisos

La API usa roles declarados por cabeceras en desarrollo y bearer token en modo integrado. Las operaciones se reducen a cuatro permisos:

| Permiso | Uso |
| --- | --- |
| `read` | Consultar contratos y artefactos del tenant. |
| `edit` | Crear borradores, evidencias, facturas, tareas y propuestas. |
| `validate` | Validar obligaciones, checks, documentos, facturas, penalidades, cambios y expedientes; aplicar cambios contractuales. |
| `export` | Descargar el paquete completo de devolucion del servicio. |

Las rutas de exportacion exigen `export` aunque sean `GET`; las rutas de resolucion/aplicacion exigen `validate`. En los `PATCH` donde el efecto depende del cuerpo, la ruta comprueba explicitamente el permiso antes de guardar.

## Modelo

```text
xfollow.contract
  ├─ obligations
  ├─ alerts
  ├─ evidence
  ├─ contract_risks (oferta adjudicataria y contraste documental)
  ├─ data_protection_assessments
  ├─ compliance_checks
  ├─ invoices
  ├─ liquidation_summary
  ├─ changes
  ├─ generated_documents
  ├─ ai_jobs
  ├─ penalty_cases
  ├─ proceedings
  ├─ ai_feedback
  ├─ governance_manifest
  ├─ tasks
  └─ audit_events
  ├─ contract_comments
  └─ contract_alert_rules
```

Las referencias a xTender, xreview o PCSP se guardan como identificadores y metadatos. No se crean claves foráneas contra los esquemas de origen para que xFollow pueda instalarse aunque una integración opcional no esté disponible.

## Trazabilidad y explicabilidad

El endpoint `/governance/manifest` expone configuracion redaccionada, modelo IA, limitaciones, permisos, formatos de devolucion y controles de supervision humana. Cada contrato tiene `/contracts/{id}/audit` y `/contracts/{id}/governance` para revisar eventos, feedback y resumen de acciones. El ZIP por contrato incluye `governance.json`, `audit.json`, `feedback.json` y `data_protection.json`.

Los documentos de la biblioteca residen únicamente en `contract_evidence`. El original se guarda bajo `data/evidence`, se identifica por hash y puede vincularse o desvincularse de una obligación sin duplicar el archivo. Al encolar una tarea se congelan contrato, datos operativos y extractos de las evidencias disponibles; la salida generada conserva las referencias documentales usadas.

La oferta adjudicataria es un `contract_evidence` con `evidence_type=winning_offer`, no una copia especial del archivo. El trabajo `offer_risk_analysis` la compara con el contrato, las obligaciones y la biblioteca disponible. Sus resultados se guardan en `contract_risks` con la oferta de origen, fuentes citadas, severidad, comparación y estado de validación humana.

`/service-return/export` y `/service-return/export.zip` generan la devolución completa del tenant: inventario de contratos, export completo por contrato, auditoría global, manifiesto de gobierno y guía de transición.
