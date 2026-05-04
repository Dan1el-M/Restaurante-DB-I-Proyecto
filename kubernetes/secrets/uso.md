# Carpeta: secrets/

## Función
Contiene **Secrets** de Kubernetes - datos sensibles encriptados (contraseñas, tokens, claves API).

## Archivos

### `restaurante-secret.yaml`
- Define secretos para:
  - **MongoDB**: usuario, contraseña
  - **PostgreSQL**: usuario, contraseña
  - **Elasticsearch**: usuario, contraseña
  - **Redis**: contraseña (si aplica)
  - **Keycloak**: contraseña admin, secreto cliente
  - **JWT**: claves para firmar tokens

## Diferencia vs ConfigMaps
| ConfigMaps | Secrets |
|-----------|---------|
| Datos públicos (URLs) | Datos sensibles (contraseñas) |
| Texto plano | Encriptados (base64 en etcd) |
| No confidencial | Confidencial |

## Seguridad
- ⚠️ **Base64 NO es encriptación**: Es solo codificación
- En producción: Usar **etcd encryption** o gestores de secretos (Vault, AWS Secrets Manager)
- Restricción de acceso: Solo ServiceAccounts autorizados pueden leerlos

## Inyección en pods
```yaml
envFrom:
  - secretRef:
      name: restaurante-secret
```
Las variables se inyectan automáticamente en el contenedor.

## Antes de hacer commit
- ⚠️ **NO commits este archivo si tiene datos reales**
- Usar `.gitignore` para excluir
- En prod: Generar secretos con herramientas de gestión
