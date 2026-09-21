# Seguridad

## Versiones

La rama `main` es la línea de desarrollo activa. Esta primera publicación no establece soporte LTS ni un plazo garantizado de respuesta.

## Comunicar una vulnerabilidad

Usa [Report a vulnerability](https://github.com/techfriendly/xFollow/security/advisories/new) para enviarla de forma privada. Incluye versión o commit, impacto, pasos de reproducción y una prueba mínima con datos sintéticos. No uses issues públicas para credenciales, datos personales o detalles de una vulnerabilidad sin corregir.

## Configuración de despliegue

Las plantillas `.env.local.example` contienen valores de desarrollo. Configura credenciales propias, identidad confiable, permisos, TLS y servicios de datos antes de exponer una instancia. Nunca pongas un token de servidor en variables `NEXT_PUBLIC_*`.

Los controles del software y las garantías del entorno se evalúan por separado. Residencia de datos, retención, certificaciones y condiciones del proveedor de IA dependen del despliegue; este repositorio no las acredita por sí mismo.
