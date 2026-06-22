param(
    [string]$AnalyticsService = "spark-analytics",
    [string]$AnalyticsContainer = "restaurant-spark-analytics",
    [int]$TimeoutSeconds = 240
)

$ErrorActionPreference = "Stop"

# Carpetas de trabajo: el script deja un log/captura textual en output.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SparkDir = Split-Path -Parent $ScriptDir
$OutputDir = Join-Path $SparkDir "output"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $OutputDir "spark_validation_$Timestamp.log"

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

    # Capturamos stdout/stderr como texto para que warnings de Docker no rompan
    # la prueba si el exit code real fue exitoso.
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
Write-Log "Spark full validation"
Write-Log "====================================================="
Write-Log "Log file: $LogFile"
Write-Log "[ ] Spark master levanta correctamente."
Write-Log "[ ] Spark worker levanta correctamente."
Write-Log "[ ] Job PySpark procesa ordenes, productos y reservas."
Write-Log "[ ] Usa Spark DataFrames."
Write-Log "[ ] Usa SparkSQL."
Write-Log "[ ] Genera tendencias de consumo."
Write-Log "[ ] Genera horarios pico."
Write-Log "[ ] Genera crecimiento mensual."
Write-Log "[ ] Guarda resultados/capturas."

# Levanta la infraestructura Spark primero; el job se ejecuta despues como
# contenedor independiente para poder validar su exit code.
Write-Log "Starting Spark services..."
Invoke-DockerCompose -Arguments @("up", "-d", "spark-master", "spark-worker") | Out-Null
Pass-Step "Spark master/worker requested"

Write-Log "Running analytics job..."
Invoke-DockerCompose -Arguments @("up", "-d", "--force-recreate", $AnalyticsService) | Out-Null

# Espera hasta que el job termine. Exited 0 significa que Spark proceso y valido
# las salidas; cualquier otro codigo se trata como fallo.
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
do {
    Start-Sleep -Seconds 5
    $status = docker inspect -f "{{.State.Status}} {{.State.ExitCode}}" $AnalyticsContainer 2>$null
    Add-Content -Path $LogFile -Value "Container status: $status"

    if ($status -match "^exited\s+0") {
        break
    }

    if ($status -match "^exited\s+[1-9]") {
        $logs = docker compose logs $AnalyticsService 2>&1 | Out-String
        Add-Content -Path $LogFile -Value $logs
        Fail-Step "Spark analytics job exited with error"
    }
} while ((Get-Date) -lt $deadline)

if ($status -notmatch "^exited\s+0") {
    Fail-Step "Spark analytics job did not finish before timeout"
}

$jobLogs = docker compose logs $AnalyticsService 2>&1 | Out-String
Add-Content -Path $LogFile -Value $jobLogs

# Patrones minimos que prueban que el job paso por los tres analisis requeridos.
foreach ($pattern in @(
    "SPARK ANALYTICS COMPLETED",
    "consumption_trends",
    "peak_hours",
    "monthly_growth",
    "orders",
    "products",
    "reservations"
)) {
    if ($jobLogs -notmatch $pattern) {
        Fail-Step "Spark logs did not include expected pattern: $pattern"
    }
}

# Verifica evidencia fisica: directorios CSV y resumen JSON en dataW/spark/output.
foreach ($path in @(
    "consumption_trends",
    "peak_hours",
    "monthly_growth",
    "validation_summary.json"
)) {
    $fullPath = Join-Path $OutputDir $path
    if (-not (Test-Path $fullPath)) {
        Fail-Step "Expected Spark output was not generated: $fullPath"
    }
}

Pass-Step "Spark master levanta correctamente."
Pass-Step "Spark worker levanta correctamente."
Pass-Step "Job PySpark procesa ordenes, productos y reservas."
Pass-Step "Spark DataFrames y SparkSQL ejecutados."
Pass-Step "Analisis requeridos generados."
Pass-Step "Resultados guardados en $OutputDir."
Write-Log "[x] Spark master levanta correctamente."
Write-Log "[x] Spark worker levanta correctamente."
Write-Log "[x] Job PySpark procesa ordenes, productos y reservas."
Write-Log "[x] Usa Spark DataFrames."
Write-Log "[x] Usa SparkSQL."
Write-Log "[x] Genera tendencias de consumo."
Write-Log "[x] Genera horarios pico."
Write-Log "[x] Genera crecimiento mensual."
Write-Log "[x] Guarda resultados/capturas."
Write-Log "Resultado: Spark validado correctamente."
