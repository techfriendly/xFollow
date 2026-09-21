# Matriz de Cumplimiento xFollow

Este documento resume como xFollow cubre el servicio de seguimiento y control de la ejecucion contractual y los requisitos transversales del producto.

## Servicios Funcionales

| Requisito | Cobertura en xFollow | Evidencia |
| --- | --- | --- |
| Alertas de vencimiento de plazos parciales, duracion, prorrogas y preavisos | Extraccion de obligaciones desde contrato, generacion de alertas con fechas, severidad y estado, y tareas derivadas. | `POST /contracts/{id}/obligations/extract`, `GET /contracts/{id}/alerts`, `POST /contracts/{id}/tasks/generate`, UI `Alertas` y `Tareas`. |
| Verificacion de plazos, obligaciones, condiciones de ejecucion y garantia | Obligaciones validadas, evidencias con hash/extraccion, checks de cumplimiento con razonamiento, citas y estado revisable. | `contract_obligations`, `contract_evidence`, `compliance_checks`, UI `Obligaciones` y `Cumplimiento`. |
| Actas de recepcion e informes de liquidacion | Generacion de documentos revisables y exportables a DOCX; liquidacion economica desde contrato, facturas, penalidades y checks. | `recepcion_acta`, `liquidacion_informe`, `GET /contracts/{id}/liquidation`, `GET /generated-documents/{id}/docx`. |
| Informes juridicos de modificacion y prorroga | Propuestas de cambio, informe juridico asociado, validacion y aplicacion controlada al contrato. | `contract_changes`, `POST /changes/{id}/report`, `PATCH /changes/{id}`, `POST /changes/{id}/apply`, UI `Cambios`. |
| Calculo de penalidades | Calculo por importe diario, dias, base/porcentaje y tope; trazabilidad del metodo y validacion humana. | `POST /contracts/{id}/penalty-cases/calculate`, `penalty_cases.calculation`, UI `Penalidades`. |
| Tramitacion de expedientes de penalidad o resolucion | Apertura, estados de tramitacion, timeline, documentos asociados y auditoria. | `contract_proceedings`, `POST /contracts/{id}/proceedings`, `PATCH /proceedings/{id}`, UI `Expedientes`. |

## Requisitos Transversales

| Requisito | Cobertura en xFollow | Evidencia |
| --- | --- | --- |
| Supervision humana | Todo resultado asistido nace como `draft`; validar, aplicar cambios, resolver checks, facturas, penalidades, expedientes y revisiones sensibles exige permiso `validate`. | `security.py`, rutas `PATCH`/`POST apply`, manifiesto `/governance/manifest`. |
| Transparencia y explicabilidad | Las verificaciones incluyen razonamiento y citas; los documentos contienen trazas y se etiquetan como borradores revisables; el manifiesto expone modelo, limitaciones y permisos. | `compliance_checks.reasoning`, `generated_documents.prompt_trace`, `GET /contracts/{id}/governance`. |
| Feedback inmediato | Feedback por artefacto sobre checks y documentos, resumen por contrato y auditoria. | `POST /feedback`, `GET /contracts/{id}/feedback`, UI `Cumplimiento`, `Documentos`, `Gobierno`. |
| Proteccion de datos y confidencialidad | Escaneo local de ficha/evidencias para emails, DNI/NIE, telefonos, IBAN y senales de confidencialidad; vista redactada y resolucion auditable. | `data_protection_assessments`, `POST /contracts/{id}/data-protection/scan`, UI `Datos`. |
| Seguridad y separacion de tenants | Roles por permiso, aislamiento por `tenant_id`, exportacion restringida y secretos redactados en configuracion. | `ROLE_PERMISSIONS`, tests de aislamiento, `/config/runtime`. |
| Entorno de IA cerrado y ubicacion UE | El manifiesto declara los controles que debe acreditar el despliegue productivo: region UE, no reutilizacion para entrenamiento, retencion limitada y confidencialidad. | `/governance/manifest.security.deployment_controls`. |
| Alfabetizacion y uso responsable | Guia funcional para usuarios, limitaciones, flujo de validacion, feedback y tratamiento de datos. | `docs/USER_GUIDE.md`, `README.md`, `/governance/manifest.ai_literacy`. |
| Devolucion ordenada del servicio | Export JSON/ZIP por contrato y paquete global del tenant con datos, documentos DOCX/Markdown, auditoria, gobierno y guia de transicion. | `GET /contracts/{id}/export.zip`, `GET /service-return/export.zip`, `transition/README.md`. |

## Condiciones de despliegue

- La extracción de obligaciones, verificación y redacción asistidas utilizan el LLM configurado a través del worker. El modo en memoria se reserva a pruebas; la operación persistente necesita PostgreSQL y las fuentes de la instalación.
- La acreditacion ENS, region UE y garantias contractuales del proveedor de IA dependen del entorno de despliegue.
- El OCR avanzado para documentos escaneados como imagen no esta incluido en el pack local; PDF/DOCX/texto si se extraen en el backend.
