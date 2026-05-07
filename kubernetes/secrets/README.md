# Secrets y .env

Por politica del curso, no se versionan passwords en YAML. El archivo principal para configurar el proyecto es el `.env` de la raiz.

## Como funciona con Kubernetes

`kubernetes/_initK8s.ps1` lee `.env` y genera automaticamente:
- `restaurante-config`: variables no sensibles.
- `restaurante-secret`: passwords, secrets, tokens y URLs sensibles como `POSTGRES_URL`.

Si queres separar secretos localmente, podes crear `kubernetes/secrets/.env.secret` copiando `kubernetes/secrets/.env.secret.example`. Sus valores reemplazan los del `.env` solo durante el init de Kubernetes.

Para levantar Kubernetes:
- `powershell -ExecutionPolicy Bypass -File kubernetes/_initK8s.ps1`

## Que variables van aqui

- `POSTGRES_PASSWORD`
- `POSTGRES_URL` (contiene password)
- `MONGO_PASSWORD` (si aplica)
- `KEYCLOAK_ADMIN_USER`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_CLIENT_SECRET` (si aplica)
- `SEED_ADMIN_PASSWORD`
