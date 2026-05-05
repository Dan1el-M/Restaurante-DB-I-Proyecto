# Carpeta: config/

## Función
Almacena **ConfigMaps** de Kubernetes que contienen datos de configuración no sensibles en formato clave-valor.

## Archivos

### `keycloak-realm-configmap.yaml`
- Contiene la configuración del **realm de Keycloak** (autenticación y autorización)
- Incluye roles, usuarios, políticas y configuraciones de seguridad
- Se monta en el pod de Keycloak para inicializar el servidor

### `restaurante-configmap.yaml`
- Variables de configuración de la aplicación (URLs, puertos, endpoints)
- Variables de entorno que no son sensibles (nombre del servicio, rutas de API)
- Se inyecta en los pods de API y Search

## Cuándo modificar
- Cambios en URLs de servicios internos
- Modificaciones en nombres de namespaces o servicios
- Actualización de rutas de la API (`ROOT_PATH`, etc.)

## Cuándo NO usar
- Para datos sensibles → usar `secrets/` en su lugar
- Para valores que varían por entorno → considerar usar variables dinámicas
