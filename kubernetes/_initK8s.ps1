$ErrorActionPreference = "Stop"

Write-Host "==> Kubernetes init (namespace: restaurante)"

Write-Host "==> [0/6] Verificando kubectl context..."
kubectl config current-context | Out-Host

Write-Host "==> [1/6] Build de imagen local para API/Search..."
docker build -t restaurante-api:local -f backend/dockerfile backend

Write-Host "==> [2/6] Namespace..."
kubectl apply -f kubernetes/namespaces/

Write-Host "==> [3/6] ConfigMaps/Secrets base..."
kubectl apply -f kubernetes/config/

$secretEnvFile = "kubernetes/secrets/.env.secret"
if (-not (Test-Path $secretEnvFile)) {
  Write-Error "Falta $secretEnvFile. Copiá kubernetes/secrets/.env.secret.example a .env.secret y llená los valores."
}

Write-Host "==> [3/6] Secret (desde .env.secret, no versionado)..."
kubectl -n restaurante create secret generic restaurante-secret `
  --from-env-file=$secretEnvFile `
  --dry-run=client -o yaml | kubectl apply -f -

Write-Host "==> [3.1/6] ConfigMap de Keycloak realm desde archivo (override del placeholder)..."
kubectl -n restaurante create configmap keycloak-realm `
  --from-file=restaurant-realm.json=backend/app/restaurant-realm.json `
  --dry-run=client -o yaml | kubectl apply -f -

Write-Host "==> [4/6] Storage + DBs..."
kubectl apply -f kubernetes/storage/
kubectl apply -f kubernetes/databases/ -R

Write-Host "==> [5/6] Servicios (API/Search/Keycloak)..."
kubectl apply -f kubernetes/services/ -R

Write-Host "==> [6/6] Ingress..."
kubectl apply -f kubernetes/ingress/

Write-Host ""
Write-Host "==> Estado (pods/svcs/ingress):"
kubectl -n restaurante get pods | Out-Host
kubectl -n restaurante get svc | Out-Host
kubectl -n restaurante get ingress | Out-Host

Write-Host ""
Write-Host "NOTAS:"
Write-Host "- Si ves que Ingress no enruta, instala un Ingress Controller (NGINX Ingress) en tu cluster."
Write-Host "- URLs esperadas (cuando el Ingress Controller esté activo): http://localhost/api/docs y http://localhost/search/docs"

#comando para levanrlo
#powershell -ExecutionPolicy Bypass -File kubernetes/_initK8s.ps1

#para ver los pods activos
#kubectl get pods -A

#para bajarlos todos ya es:
#kubectl delete namespace restaurante
