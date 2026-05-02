# CI/CD para Restaurante-DB-I-Proyecto

## ¿Dónde crear los archivos?

- Pipeline principal: `.github/workflows/ci-cd.yml`
- Pruebas unitarias: `backend/tests/unit/`
- Pruebas de integración: `backend/tests/integration/`

## ¿Para qué sirve cada parte?

1. `unit-tests`: valida funciones aisladas de Python.
2. `integration-tests`: valida contrato de endpoints HTTP (`/health`, `/ping`).
3. `docker-build-and-push`: construye imagen Docker y la publica en GHCR.

## Configuración requerida en GitHub

1. Ir a **Settings → Actions → General** y permitir Actions.
2. Ir a **Settings → Actions → General → Workflow permissions** y seleccionar:
   - `Read and write permissions`
3. Ir a **Settings → Packages** (opcional) para confirmar acceso a GHCR.
4. Usar rama `main` para publicación automática.

## Flujo recomendado paso a paso

1. Crear una rama de trabajo.
2. Agregar los archivos de pipeline y tests.
3. Hacer commit y push.
4. Abrir Pull Request hacia `main`.
5. Validar jobs en pestaña **Actions**.
6. Al mergear a `main`, se publica imagen en `ghcr.io/<owner>/<repo>`.
7. En local, actualizar proyecto y ejecutar:

```bash
docker compose pull

docker compose up -d --build
```

## ¿Cómo probar que está bien implementado?

- En PR: deben pasar `unit-tests` e `integration-tests`.
- En `main`: debe pasar además `docker-build-and-push`.
- En GHCR: debe aparecer una imagen nueva con tag de rama o SHA.
- En local: `curl http://localhost:8000/health` debe responder `{"status":"ok"}`.
