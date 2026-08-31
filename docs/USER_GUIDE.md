# Guia Funcional xFollow

## Instalacion

Desde `xFollow/`, copia `.env.local.example` a `.env.local` y arranca la instancia:

```bash
cp .env.local.example .env.local
docker compose --env-file .env.local up --build -d
```

Abre `http://localhost:3101`. El selector superior `Proyecto activo` conserva el contrato elegido al cambiar de modulo. Ese nombre representa el contrato de trabajo actual y no crea una segunda entidad en la base compartida.

La API usa `POSTGRES_DSN_DOCKER` dentro del contenedor y crea solo `xfollow`. Si las tablas de xTender, xreview o PCSP no están disponibles, se pueden crear contratos manualmente y el resto del flujo sigue operativo.

## Centro de trabajo

En `Contratos`, utiliza la busqueda y los filtros combinables de texto, estado y decision de continuidad. La ficha concentra responsables, fechas, importes, garantias, alertas, obligaciones, facturas, documentos, tareas y trazabilidad.

Los comentarios de la ficha sirven para dejar decisiones y contexto operativo. Las reglas de alerta se guardan por tenant y pueden compartirse con el equipo.

## Flujo Recomendado

1. Crear o importar un contrato desde xTender o PCSP. Si el lote ya ha sido adjudicado en xreview, usa el botón con el mazo de la topbar: selecciona el paquete publicado y xfollow enlazará automáticamente la oferta ganadora, incorporará los compromisos aceptados como obligaciones y pondrá en cola su análisis de riesgos.
2. Extraer obligaciones e hitos, revisar el contenido propuesto y validar solo lo correcto.
3. Revisar alertas y generar tareas internas para plazos, evidencias pendientes y riesgos.
4. En `Documentos`, subir evidencias en PDF, DOCX, texto o Markdown; el sistema guarda hash y texto extraído y permite vincular o desvincular la obligación después. Selecciona `Oferta adjudicataria` al cargar la propuesta ganadora.
5. Ejecutar revisiones de datos antes de compartir evidencias o usarlas en procesos asistidos.
6. Usar `Extraer con IA`, `Verificar con IA` y `Generar con IA` cuando corresponda. La operación queda en cola, muestra su estado y se actualiza al finalizar; revisar siempre las fuentes y validar o rechazar el resultado.
7. Desde la oferta adjudicataria, usar `Analizar oferta con IA` para contrastar compromisos, alcance, plazos, recursos, calidad, aspectos económicos y jurídicos frente al contrato y la biblioteca. Validar cada riesgo antes de usarlo operativamente.
8. Registrar facturas, conformarlas, marcar pago y revisar la liquidacion.
9. Proponer prórrogas o modificaciones, usar `Generar informe con IA`, validar y aplicar.
10. Calcular penalidades si procede y abrir el expediente correspondiente.
11. Generar actas, informes y documentos de expediente, descargarlos en DOCX y validar su version final.
12. Usar el modulo de gobierno para revisar auditoria, permisos, feedback y exportar la devolucion.

## Validacion Humana

xFollow no toma decisiones administrativas por si mismo. Las salidas asistidas son borradores y deben revisarse por una persona competente antes de tener efecto operativo.

Si `llm2` no está disponible, el estado lateral lo indicará y los trabajos se reintentarán automáticamente. Los errores no transitorios quedan visibles en la lista de trabajos y se pueden relanzar cuando se haya corregido su causa.

Acciones que requieren especial revision:

- Validar obligaciones, checks y documentos.
- Conformar o pagar facturas.
- Validar penalidades.
- Validar y aplicar modificaciones o prorrogas.
- Avanzar expedientes de penalidad o resolucion.
- Resolver hallazgos de proteccion de datos o confidencialidad.

## Proteccion De Datos

El modulo `Datos` escanea ficha contractual y evidencias para localizar posibles datos personales o senales de confidencialidad. La previsualizacion redacta coincidencias comunes para facilitar la revision.

Buenas practicas:

- Subir solo evidencias necesarias para el seguimiento.
- Revisar metadatos de documentos antes de compartirlos fuera del entorno.
- Resolver cada hallazgo con comentario cuando se haya anonimizado, aceptado el riesgo o descartado el falso positivo.
- Evitar enviar documentos con datos personales a modelos externos si el proveedor no acredita entorno cerrado, no reutilizacion y retencion limitada.

## Feedback Y Mejora

Cuando una verificacion o documento sea util, incorrecto o incompleto, registra feedback desde el modulo correspondiente. El feedback queda vinculado al contrato y aparece en gobierno para orientar ajustes del sistema.

## Devolucion Del Servicio

La exportacion por contrato genera ZIP con JSON, auditoria, evidencias logicas, revisiones de datos, documentos Markdown y DOCX. La exportacion global incluye todo el tenant y una guia de transicion.
