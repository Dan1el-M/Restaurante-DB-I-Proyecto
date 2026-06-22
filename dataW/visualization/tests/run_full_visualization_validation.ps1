param(
    [int]$SupersetPort = 8088,
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"

# Este script valida la infraestructura del punto 3:
# 1. Docker Compose es valido.
# 2. Hive y el warehouse estan levantados.
# 3. Las vistas OLAP responden consultas.
# 4. Superset queda disponible desde navegador.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VisualizationDir = Split-Path -Parent $ScriptDir
$OutputDir = Join-Path $VisualizationDir "output"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $OutputDir "visualization_validation_$Timestamp.log"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Fail-Step {
    param([string]$Message)
    Write-Log "[FAIL] $Message"
    throw $Message
}

function Pass-Step {
    param([string]$Message)
    Write-Log "[OK] $Message"
}

function Invoke-DockerCompose {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = docker compose @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $text = ($output | Out-String)
    Add-Content -Path $LogFile -Value $text

    if ($exitCode -ne 0) {
        Write-Log $text
        Fail-Step "docker compose $($Arguments -join ' ') failed with exit code $exitCode"
    }

    return $text
}

Write-Log "====================================================="
Write-Log "Visualization BI full validation"
Write-Log "====================================================="
Write-Log "Log file: $LogFile"
Write-Log "[ ] Docker Compose contiene Superset."
Write-Log "[ ] Hive warehouse responde."
Write-Log "[ ] Vistas OLAP responden consultas."
Write-Log "[ ] Superset levanta correctamente."
Write-Log "[ ] Superset queda disponible via web."

Write-Log "Validating Docker Compose syntax..."
Invoke-DockerCompose -Arguments @("config", "--quiet") | Out-Null
Pass-Step "Docker Compose syntax is valid."

Write-Log "Starting Hive warehouse and Superset services..."
Invoke-DockerCompose -Arguments @("up", "-d", "hiveserver2", "warehouse-setup", "superset-init", "superset") | Out-Null
Pass-Step "Compose services requested."

Write-Log "Checking OLAP views from Hive..."
$hiveQuery = @"
USE restaurant_warehouse;
SELECT 'cubo_ingresos_mes_categoria' AS view_name, COUNT(*) AS total_rows FROM cubo_ingresos_mes_categoria;
SELECT 'cubo_actividad_clientes_zona' AS view_name, COUNT(*) AS total_rows FROM cubo_actividad_clientes_zona;
SELECT 'cubo_ordenes_completadas_canceladas' AS view_name, COUNT(*) AS total_rows FROM cubo_ordenes_completadas_canceladas;
"@

$hiveOutput = $hiveQuery | docker exec -i hiveserver2 /opt/hive/bin/beeline -u "jdbc:hive2://localhost:10000/restaurant_warehouse" 2>&1 | Out-String
Add-Content -Path $LogFile -Value $hiveOutput

if ($LASTEXITCODE -ne 0) {
    Write-Log $hiveOutput
    Fail-Step "Hive OLAP view validation failed."
}

foreach ($viewName in @(
    "cubo_ingresos_mes_categoria",
    "cubo_actividad_clientes_zona",
    "cubo_ordenes_completadas_canceladas"
)) {
    if ($hiveOutput -notmatch $viewName) {
        Fail-Step "Hive output did not include expected view: $viewName"
    }
}

Pass-Step "Hive warehouse and OLAP views respond."

Write-Log "Waiting for Superset web UI..."
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$supersetUrl = "http://localhost:$SupersetPort/health"
$healthy = $false

do {
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri $supersetUrl -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            $healthy = $true
            break
        }
    }
    catch {
        Add-Content -Path $LogFile -Value $_.Exception.Message
    }
} while ((Get-Date) -lt $deadline)

if (-not $healthy) {
    $logs = Invoke-DockerCompose -Arguments @("logs", "--tail=200", "superset")
    Add-Content -Path $LogFile -Value $logs
    Fail-Step "Superset did not become available at $supersetUrl"
}

Pass-Step "Superset web UI is available at http://localhost:$SupersetPort."
Write-Log "[x] Docker Compose contiene Superset."
Write-Log "[x] Hive warehouse responde."
Write-Log "[x] Vistas OLAP responden consultas."
Write-Log "[x] Superset levanta correctamente."
Write-Log "[x] Superset queda disponible via web."
Write-Log "Resultado: Visualizacion BI validada correctamente."
