# Carpeta: services/keycloak/

## Función
Manifiestos para **Keycloak** - servidor de autenticación y autorización (OAuth2, OpenID Connect).

## Archivos

### `keycloak-deployment.yaml`
- **Imagen**: `keycloak/keycloak:latest`
- **Puerto**: 8080 (HTTP)
- **Variables de entorno**:
  - `KEYCLOAK_ADMIN`: Usuario administrador
  - `KEYCLOAK_ADMIN_PASSWORD`: Contraseña admin
  - `DB_VENDOR`, `DB_ADDR`, `DB_PORT`: Conexión a BD
  - `KEYCLOAK_REALM_FILE`: ConfigMap del realm

### `keycloak-service.yaml`
- **Tipo**: ClusterIP
- **DNS**: `keycloak.restaurante.svc.cluster.local:8080`
- **Puerto**: 8080

## Configuración del Realm
- Archivo: `config/keycloak-realm-configmap.yaml`
- Se monta en `/opt/keycloak/data/import/`
- Keycloak lo carga automáticamente al iniciar

## Acceso a la consola admin
```bash
# Forward del puerto para acceso local
kubectl -n restaurante port-forward svc/keycloak 8080:8080

# Luego acceder a: http://localhost:8080/admin
# Usuario: keycloak_admin (o el definido)
# Contraseña: Definida en secret
```

## Funciones en tu app
- Autenticación de usuarios
- Registro de usuarios
- Gestión de roles y permisos
- Generación de JWT tokens

## Integración con FastAPI
- Ver: `backend/app/autentificador/`
