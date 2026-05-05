$ErrorActionPreference = "Stop"

Write-Host "==> Instalando NGINX Ingress Controller (namespace: ingress-nginx)"
Write-Host "Context actual:"
kubectl config current-context | Out-Host

$ns = "ingress-nginx"

Write-Host "==> [1/4] Crear namespace (si no existe)..."
kubectl get namespace $ns 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  kubectl create namespace $ns | Out-Host
} else {
  Write-Host "Namespace $ns ya existe."
}

Write-Host "==> [2/4] Aplicar manifiesto oficial del NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/cloud/deploy.yaml

Write-Host "==> [3/4] Esperar rollout..."
kubectl -n $ns rollout status deployment/ingress-nginx-controller --timeout=300s | Out-Host

Write-Host "==> [4/4] Ver servicios del ingress controller..."
kubectl -n $ns get svc | Out-Host

Write-Host ""
Write-Host "Si tu Ingress de la app ya existe, en unos segundos deberías ver ADDRESS:"
Write-Host "- `kubectl -n restaurante get ingress`"
Write-Host "Y luego abrir:"
Write-Host "- http://localhost:8001/admin/master/console/"
Write-Host "- http://localhost:8080/api/docs"
Write-Host "- http://localhost:8081/search/docs" 


#esto es paa intarla un controller de ingress para nginx, si no lo tenes instalado
#hay que instarlalo antes de correr el _initK8s.ps1, sino  va a fallar 

#comando para levanrlo
#powershell -ExecutionPolicy Bypass -File kubernetes/_installIngressNginx.ps1