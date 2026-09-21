# Datos y documentos

La distribución pública contiene código, documentación y configuración de ejemplo. Los datos de cada instalación permanecen fuera del repositorio.

No se publican anexos, pliegos, ofertas, expedientes, corpus documentales, originales, extracciones Markdown/JSON, índices vectoriales, evidencias, bases de datos, backups ni exportaciones del entorno de trabajo. Las pruebas usan contenido ficticio generado en código.

Los conectores permiten incorporar fuentes en una instalación propia. Quien configure la ingesta debe determinar los permisos y condiciones de reutilización de cada fuente. La licencia Apache 2.0 del software no relicencia documentos ni pesos de modelos externos.

`data/` está excluido de Git salvo su README. Los archivos `.env` reales también están excluidos. Revisa `git diff --cached` antes de cada contribución: `.gitignore` ayuda a evitar incorporaciones accidentales, pero no inspecciona el contenido ni borra archivos que ya estuviesen versionados.
