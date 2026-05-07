$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
  param(
    [Parameter(Mandatory = $true)][string]$Message
  )
  if ($LASTEXITCODE -ne 0) {
    throw $Message
  }
}

Write-Host "==> Kubernetes init (namespace: restaurante)"

Write-Host "==> [0/7] Verificando kubectl context..."
kubectl config current-context | Out-Host

Write-Host "==> [1/7] Build de imagen local para API/Search..."
$imageTag = "restaurante-api:local-{0}" -f (Get-Date -Format "yyyyMMddHHmmss")
docker build -t $imageTag -f backend/dockerfile backend
Assert-LastExitCode "Fallo docker build"
docker tag $imageTag restaurante-api:local | Out-Host
Write-Host "==> Imagen construida: $imageTag"

Write-Host "==> [2/7] Namespace..."
kubectl apply -f kubernetes/namespaces/
Assert-LastExitCode "Fallo aplicando kubernetes/namespaces/"

Write-Host "==> [3/7] ConfigMaps/Secrets base..."
kubectl apply -f kubernetes/config/
Assert-LastExitCode "Fallo aplicando kubernetes/config/"

$secretEnvFile = "kubernetes/secrets/.env.secret"
if (-not (Test-Path $secretEnvFile)) {
  Write-Error "Falta $secretEnvFile. Copiá kubernetes/secrets/.env.secret.example a .env.secret y llená los valores."
}

Write-Host "==> [3/7] Secret (desde .env.secret, no versionado)..."
kubectl -n restaurante create secret generic restaurante-secret --from-env-file=$secretEnvFile --dry-run=client -o yaml | kubectl apply -f -

Write-Host "==> [3.1/7] ConfigMap de Keycloak realm desde archivo (override del placeholder)..."
kubectl -n restaurante create configmap keycloak-realm --from-file=restaurant-realm.json=backend/app/restaurant-realm.json --dry-run=client -o yaml | kubectl apply -f -

Write-Host "==> [4/7] Storage + DBs..."
kubectl apply -f kubernetes/storage/
Assert-LastExitCode "Fallo aplicando kubernetes/storage/"

# Re-ejecutar jobs de init si ya existían (kubectl apply no recrea Jobs completados/fallidos)
Write-Host "==> [4.0/6] Reiniciando Jobs de DB (si existen)..."
kubectl -n restaurante delete job mongo-cluster-init --ignore-not-found | Out-Host
# Limpia el Mongo "single node" legacy si existÃ­a (evita conflictos al aplicar el shardeado)
kubectl -n restaurante delete statefulset mongo --ignore-not-found | Out-Host
kubectl -n restaurante delete svc mongo --ignore-not-found | Out-Host

# Aplica DBs (evita aplicar manifests legacy en kubernetes/databases/mongo/)
kubectl apply -f kubernetes/databases/elasticsearch/
Assert-LastExitCode "Fallo aplicando kubernetes/databases/elasticsearch/"
kubectl apply -f kubernetes/databases/postgres/
Assert-LastExitCode "Fallo aplicando kubernetes/databases/postgres/"
kubectl apply -f kubernetes/databases/redis/
Assert-LastExitCode "Fallo aplicando kubernetes/databases/redis/"
kubectl apply -f kubernetes/databases/mongo/mongo-sharded-cluster.yaml
Assert-LastExitCode "Fallo aplicando kubernetes/databases/mongo/mongo-sharded-cluster.yaml"

Write-Host "==> [4.05/6] Esperando Mongo (cfg/shard/mongos) listo..."
kubectl -n restaurante rollout status statefulset/mongo-cfg --timeout=10m | Out-Host
kubectl -n restaurante rollout status statefulset/mongo-shard1 --timeout=10m | Out-Host
kubectl -n restaurante rollout status deployment/mongos --timeout=10m | Out-Host

Write-Host "==> [4.1/6] Esperando init de Mongo shardeado (mongo-cluster-init)..."
kubectl -n restaurante wait --for=condition=complete job/mongo-cluster-init --timeout=20m | Out-Host

Write-Host "==> [5/7] Servicios base (Keycloak/API/Search, sin seed)..."
kubectl apply -f kubernetes/services/keycloak/
Assert-LastExitCode "Fallo aplicando kubernetes/services/keycloak/"
$apiYaml = (Get-Content -Raw -LiteralPath kubernetes/services/api/api-deployment.yaml) -replace "restaurante-api:local", $imageTag
$apiYaml | kubectl apply -f -
Assert-LastExitCode "Fallo aplicando kubernetes/services/api/api-deployment.yaml"
kubectl apply -f kubernetes/services/api/api-service.yaml
Assert-LastExitCode "Fallo aplicando kubernetes/services/api/api-service.yaml"
kubectl apply -f kubernetes/services/api/api-lb-service.yaml
Assert-LastExitCode "Fallo aplicando kubernetes/services/api/api-lb-service.yaml"
$searchYaml = (Get-Content -Raw -LiteralPath kubernetes/services/search/search-deployment.yaml) -replace "restaurante-api:local", $imageTag
$searchYaml | kubectl apply -f -
Assert-LastExitCode "Fallo aplicando kubernetes/services/search/search-deployment.yaml"
kubectl apply -f kubernetes/services/search/search-service.yaml
Assert-LastExitCode "Fallo aplicando kubernetes/services/search/search-service.yaml"
kubectl apply -f kubernetes/services/search/search-lb-service.yaml
Assert-LastExitCode "Fallo aplicando kubernetes/services/search/"

Write-Host "==> [5.1/7] Esperando Keycloak listo..."
kubectl -n restaurante rollout status deployment/keycloak --timeout=600s | Out-Host

Write-Host "==> [5.2/7] Reiniciando Job seed-admin..."
kubectl -n restaurante delete job seed-admin --ignore-not-found=true | Out-Host
$seedYaml = (Get-Content -Raw -LiteralPath kubernetes/services/api/seed-job.yaml) -replace "restaurante-api:local", $imageTag
$seedYaml | kubectl apply -f -
Assert-LastExitCode "Fallo aplicando kubernetes/services/api/seed-job.yaml"

Write-Host "==> [5.3/7] Esperando seed-admin..."

$seedTimeoutSeconds = 420
if ($env:SEED_WAIT_SECONDS) {
  try { $seedTimeoutSeconds = [int]$env:SEED_WAIT_SECONDS } catch {}
}
$start = Get-Date
$lastLogAt = Get-Date "1970-01-01"

while ($true) {
  $succeeded = kubectl -n restaurante get job seed-admin -o jsonpath="{.status.succeeded}" 2>$null
  $failed = kubectl -n restaurante get job seed-admin -o jsonpath="{.status.failed}" 2>$null

  if ($succeeded -eq "1") {
    break
  }

  $failedCount = 0
  if ($failed) {
    $failedCount = [int]$failed
  }

  if ($failedCount -ge 1) {
    Write-Host "ERROR: seed-admin falló. Mostrando diagnóstico..."
    kubectl -n restaurante get pods -l job-name=seed-admin -o wide | Out-Host
    kubectl -n restaurante logs job/seed-admin --all-containers=true --tail=300 | Out-Host
    throw "Seed-admin falló"
  }

  $elapsed = (New-TimeSpan -Start $start -End (Get-Date)).TotalSeconds

  # Mostrar progreso sin esperar a timeout (tail corto cada ~15s)
  $sinceLastLog = (New-TimeSpan -Start $lastLogAt -End (Get-Date)).TotalSeconds
  if ($sinceLastLog -ge 15) {
    Write-Host ("[seed-admin] esperando... {0:N0}s" -f $elapsed)
    try {
      # Puede fallar mientras el pod está en ContainerCreating; no debe tumbar el init.
      kubectl -n restaurante logs job/seed-admin --all-containers=true --tail=25 2>$null | Out-Host
    } catch {
      Write-Host ("[seed-admin] logs no disponibles todavía: {0}" -f $_.Exception.Message)
    }
    $lastLogAt = Get-Date
  }

  if ($elapsed -ge $seedTimeoutSeconds) {
    Write-Host "ERROR: seed-admin no completó en ${seedTimeoutSeconds}s. Mostrando diagnóstico..."
    kubectl -n restaurante describe job seed-admin | Out-Host
    kubectl -n restaurante get pods -l job-name=seed-admin -o wide | Out-Host
    kubectl -n restaurante logs job/seed-admin --all-containers=true --tail=300 | Out-Host
    throw "Seed-admin timeout"
  }

  Start-Sleep -Seconds 3
}

Write-Host "==> [6/7] Ingress..."
kubectl apply -f kubernetes/ingress/
Assert-LastExitCode "Fallo aplicando kubernetes/ingress/"

Write-Host ""
Write-Host "==> Estado (pods/svcs/ingress/jobs):"
kubectl -n restaurante get pods | Out-Host
kubectl -n restaurante get jobs | Out-Host
kubectl -n restaurante get svc | Out-Host
kubectl -n restaurante get ingress | Out-Host

Write-Host "Y luego abrir:"
Write-Host "- http://localhost:8001/admin/master/console/"
Write-Host "- http://localhost:8080/api/docs"
Write-Host "- http://localhost:8081/search/docs" 
Write-Host ""
Write-Host "NOTAS:"
Write-Host "- Si ves que Ingress no enruta, instala un Ingress Controller (NGINX Ingress) en tu cluster."
Write-Host "- URLs esperadas (cuando el Ingress Controller esté activo): http://localhost/api/docs y http://localhost/search/docs"

#comando para levanrlo
#powershell -ExecutionPolicy Bypass -File kubernetes/_initK8s.ps1

#para ver los pods activos
#kubectl get pods -A

#para bajarlos todos ya es:
# kubectl delete namespace restaurante

#rutas que hay que levantar
#http://localhost:8001/admin/master/console/ 
#http://localhost:8080/api/docs 
#http://localhost:8081/search/docs 
Write-Host "- http://localhost:8081/search/docs"
Write-Host "- http://localhost:8000/docs (modo directo/compose)"
