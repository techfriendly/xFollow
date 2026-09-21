# Componentes de terceros

La licencia Apache 2.0 se aplica al código propio de este repositorio. Las dependencias se obtienen por separado y conservan sus licencias, avisos y condiciones. Este documento identifica un punto material y los manifiestos que deben acompañar la revisión de cada entrega; no es un inventario exhaustivo de dependencias transitivas.

## Procesamiento PDF: PyMuPDF / MuPDF

Los tres módulos utilizan PyMuPDF. xTender también utiliza PyMuPDF4LLM, basado en PyMuPDF. PyMuPDF/MuPDF se ofrecen bajo AGPL o licencia comercial, según la [documentación oficial de licencias](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright).

No debe presentarse un paquete combinado que los utilice como sujeto únicamente a Apache 2.0. Según la forma de combinación, distribución y prestación del servicio, pueden aplicarse las obligaciones de AGPL, incluida la provisión del código fuente correspondiente. Una distribución que no vaya a cumplir esas obligaciones necesita derechos comerciales suficientes del proveedor o sustituir los componentes afectados. No se presupone que una licencia comercial exista ni que pueda transferirse.

## Manifiestos de la entrega

En los repositorios de aplicación, `package-lock.json` fija las dependencias de frontend; `apps/api/requirements.txt` y, en xTender, `apps/embedding_api/requirements.txt` declaran las dependencias Python. Estas últimas admiten rangos: el conjunto exacto debe registrarse en el entorno entregado. `docker-compose.yml` y los Dockerfiles identifican imágenes y servicios.

Conserva los textos y avisos de licencia de las versiones efectivamente distribuidas. Los servicios de datos y los pesos de modelos también requieren revisar sus propias condiciones. No se entregan pesos de modelos en estos repositorios.

Los documentos incorporados por cada instalación no quedan relicenciados por la licencia del software.
