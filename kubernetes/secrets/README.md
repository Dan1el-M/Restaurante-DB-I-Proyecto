# Secrets (no hardcode)

Por política del curso, **no se versionan passwords** en YAML.

## Cómo crear el Secret
1) Copiar el ejemplo:
- Copiá `kubernetes/secrets/.env.secret.example` a `kubernetes/secrets/.env.secret`

2) Editar valores reales en `kubernetes/secrets/.env.secret`

3) Crear/actualizar el secret en el cluster:
- `kubectl -n restaurante create secret generic restaurante-secret --from-env-file=kubernetes/secrets/.env.secret --dry-run=client -o yaml | kubectl apply -f -`

## Qué variables van aquí
- `POSTGRES_PASSWORD`
- `POSTGRES_URL` (contiene password)
- `MONGO_PASSWORD` (si aplica)
- `KEYCLOAK_ADMIN_USER`
- `KEYCLOAK_ADMIN_PASSWORD`

