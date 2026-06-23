param(
    [string]$ContainerName = "hiveserver2",
    [string]$DatabaseName = "restaurant_warehouse",
    [string]$HiveJdbcHost = "localhost",
    [int]$HiveJdbcPort = 10000,
    [string]$HiveImage = "apache/hive:4.0.0",
    [int]$StartupWaitSeconds = 30
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WarehouseDir = Split-Path -Parent $ScriptDir
$OutputDir = Join-Path $ScriptDir "output"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $OutputDir "dw_validation_$Timestamp.log"

$ContainerWarehouseDir = "/workspace/warehouse"
$SchemaFile = "$ContainerWarehouseDir/schemas/schema_star.sql"
$ViewsFile = "$ContainerWarehouseDir/schemas/hive_olap_views.sql"
$SeedFile = "$ContainerWarehouseDir/generated/operational_seed.hql"
$ValidationFile = "$ContainerWarehouseDir/tests/validacion_requisitos_olap.hql"
$DefaultJdbcUrl = "jdbc:hive2://$HiveJdbcHost`:$HiveJdbcPort/default"
$WarehouseJdbcUrl = "jdbc:hive2://$HiveJdbcHost`:$HiveJdbcPort/$DatabaseName"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Write-Section {
    param([string]$Title)
    Write-Log ""
    Write-Log "====================================================="
    Write-Log $Title
    Write-Log "====================================================="
}

function Pass-Step {
    param([string]$Message)
    Write-Log "[OK] $Message"
}

function Fail-Step {
    param([string]$Message)
    Write-Log "[FAIL] $Message"
    throw $Message
}

function Invoke-CheckedCommand {
    param(
        [string]$Title,
        [string[]]$Command,
        [string[]]$RequiredPatterns = @()
    )

    Write-Section $Title
    Write-Log ("Command: " + ($Command -join " "))

    $executable = $Command[0]
    $arguments = $Command[1..($Command.Length - 1)]
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $executable @arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    $text = ($output | Out-String)

    Add-Content -Path $LogFile -Value $text

    if ($exitCode -ne 0) {
        Write-Log $text
        Fail-Step "$Title failed with exit code $exitCode"
    }

    if ($text -match "(?m)(^Error:|FAILED:|SemanticException|ParseException|Table not found)") {
        Write-Log $text
        Fail-Step "$Title contains Hive errors"
    }

    foreach ($pattern in $RequiredPatterns) {
        if ($text -notmatch $pattern) {
            Write-Log $text
            Fail-Step "$Title did not include expected pattern: $pattern"
        }
    }

    Pass-Step $Title
    return $text
}

function Invoke-Beeline {
    param(
        [string]$Title,
        [string]$JdbcUrl,
        [string]$Sql,
        [string]$File,
        [string[]]$RequiredPatterns = @()
    )

    $command = @("docker", "exec", "-i", $ContainerName, "beeline", "-u", $JdbcUrl)

    if ($Sql) {
        $command += @("-e", $Sql)
    }

    if ($File) {
        $command += @("-f", $File)
    }

    Invoke-CheckedCommand -Title $Title -Command $command -RequiredPatterns $RequiredPatterns
}

function Get-ContainerRunning {
    param([string]$Name)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $status = docker inspect -f "{{.State.Running}}" $Name 2>$null
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($exitCode -ne 0) {
        return $null
    }

    return ($status -eq "true")
}

function New-HiveContainer {
    Write-Log "Creating Hive container '$ContainerName' from $HiveImage..."

    $dockerArgs = @(
        "run", "-d",
        "--name", $ContainerName,
        "-p", "$HiveJdbcPort`:10000",
        "-p", "10002:10002",
        "-e", "SERVICE_NAME=hiveserver2",
        "-v", "$WarehouseDir`:$ContainerWarehouseDir",
        $HiveImage
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = docker @dockerArgs 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    Add-Content -Path $LogFile -Value (($output | Out-String))

    if ($exitCode -ne 0) {
        Fail-Step "Could not create Hive container. Check Docker Desktop and port $HiveJdbcPort."
    }
}

function Ensure-HiveContainer {
    $running = Get-ContainerRunning -Name $ContainerName

    if ($null -eq $running) {
        Write-Log "Container '$ContainerName' does not exist."
        New-HiveContainer
    }
    elseif ($running -eq $false) {
        Write-Log "Container '$ContainerName' is stopped. Trying docker start..."
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            docker start $ContainerName | Out-Null
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }

        Write-Log "Waiting $StartupWaitSeconds seconds for HiveServer2..."
        Start-Sleep -Seconds $StartupWaitSeconds

        $running = Get-ContainerRunning -Name $ContainerName
        if ($running -ne $true) {
            Write-Log "Container stopped again. Recreating it with the expected volume and ports..."
            docker rm -f $ContainerName | Out-Null
            New-HiveContainer
        }
    }

    Write-Log "Waiting $StartupWaitSeconds seconds for HiveServer2..."
    Start-Sleep -Seconds $StartupWaitSeconds
}

Write-Section "Data Warehouse OLAP full validation"
Write-Log "Workspace warehouse dir: $WarehouseDir"
Write-Log "Log file: $LogFile"
Write-Log "Hive container: $ContainerName"
Write-Log "Warehouse database: $DatabaseName"

Write-Section "Checklist"
Write-Log "[ ] Hive levanta correctamente."
Write-Log "[ ] Existe la base de datos del warehouse."
Write-Log "[ ] Se crean las dimensiones."
Write-Log "[ ] Se crean las tablas de hechos."
Write-Log "[ ] Se crean los cubos/vistas OLAP."
Write-Log "[ ] Las tablas tienen datos cargados."
Write-Log "[ ] Las vistas devuelven resultados."
Write-Log "[ ] Hay consultas de prueba/capturas."

Ensure-HiveContainer

Invoke-Beeline `
    -Title "[1/8] Hive levanta correctamente" `
    -JdbcUrl $DefaultJdbcUrl `
    -Sql "SHOW DATABASES;" `
    -RequiredPatterns @("default") | Out-Null

Invoke-Beeline `
    -Title "[2/8] Crear/verificar base de datos del warehouse" `
    -JdbcUrl $DefaultJdbcUrl `
    -Sql "CREATE DATABASE IF NOT EXISTS $DatabaseName;" | Out-Null

Invoke-Beeline `
    -Title "[2/8] Existe la base de datos del warehouse" `
    -JdbcUrl $DefaultJdbcUrl `
    -Sql "SHOW DATABASES;" `
    -RequiredPatterns @($DatabaseName) | Out-Null

Invoke-Beeline `
    -Title "[3/8] Crear dimensiones y tablas de hechos" `
    -JdbcUrl $WarehouseJdbcUrl `
    -File $SchemaFile | Out-Null

Invoke-Beeline `
    -Title "[3/8] Verificar dimensiones" `
    -JdbcUrl $WarehouseJdbcUrl `
    -Sql "SHOW TABLES;" `
    -RequiredPatterns @("dim_time", "dim_customer", "dim_product", "dim_restaurant", "dim_status") | Out-Null

Invoke-Beeline `
    -Title "[4/8] Verificar tablas de hechos" `
    -JdbcUrl $WarehouseJdbcUrl `
    -Sql "SHOW TABLES;" `
    -RequiredPatterns @("fact_orders", "fact_reservations") | Out-Null

Invoke-Beeline `
    -Title "[5/8] Cargar seed de datos historicos" `
    -JdbcUrl $WarehouseJdbcUrl `
    -File $SeedFile | Out-Null

$countsSql = @"
SELECT 'dim_time' AS tabla, COUNT(*) AS total FROM dim_time
UNION ALL SELECT 'dim_customer' AS tabla, COUNT(*) AS total FROM dim_customer
UNION ALL SELECT 'dim_product' AS tabla, COUNT(*) AS total FROM dim_product
UNION ALL SELECT 'dim_restaurant' AS tabla, COUNT(*) AS total FROM dim_restaurant
UNION ALL SELECT 'dim_status' AS tabla, COUNT(*) AS total FROM dim_status
UNION ALL SELECT 'fact_orders' AS tabla, COUNT(*) AS total FROM fact_orders
UNION ALL SELECT 'fact_reservations' AS tabla, COUNT(*) AS total FROM fact_reservations;
"@

$countsOutput = Invoke-Beeline `
    -Title "[6/8] Verificar datos cargados" `
    -JdbcUrl $WarehouseJdbcUrl `
    -Sql $countsSql `
    -RequiredPatterns @("dim_time", "fact_orders", "fact_reservations")

foreach ($tableName in @("dim_time", "dim_customer", "dim_product", "dim_restaurant", "dim_status", "fact_orders", "fact_reservations")) {
    if ($countsOutput -match "\|\s*$tableName\s*\|\s*0\s*\|") {
        Fail-Step "Table $tableName has 0 rows"
    }
}
Pass-Step "All warehouse tables have data"

Invoke-Beeline `
    -Title "[7/8] Crear cubos/vistas OLAP" `
    -JdbcUrl $WarehouseJdbcUrl `
    -File $ViewsFile | Out-Null

Invoke-Beeline `
    -Title "[7/8] Verificar cubos/vistas OLAP" `
    -JdbcUrl $WarehouseJdbcUrl `
    -Sql "SHOW TABLES;" `
    -RequiredPatterns @(
        "cubo_ingresos_mes_categoria",
        "cubo_actividad_clientes_zona",
        "cubo_tendencias_horarios_pico",
        "cubo_lealtad_clientes",
        "cubo_bestsellers_productos"
    ) | Out-Null

$viewChecks = @(
    @{ Name = "Tiempo y producto"; Sql = "SELECT year, month, category, ingresos_totales FROM cubo_ingresos_mes_categoria LIMIT 5;"; Pattern = "Plato fuerte|Entrada|Bebida|Postre" },
    @{ Name = "Ubicacion"; Sql = "SELECT geographic_zone, restaurant_location, total_ordenes FROM cubo_actividad_clientes_zona LIMIT 5;"; Pattern = "Central|Oeste|Este" },
    @{ Name = "Frecuencia por hora"; Sql = "SELECT day_name, hora, ordenes_por_hora FROM cubo_tendencias_horarios_pico LIMIT 5;"; Pattern = "Friday|Saturday|Wednesday|Sunday" },
    @{ Name = "Frecuencia por cliente"; Sql = "SELECT customer_name, total_ordenes_cliente, total_reservaciones_cliente FROM cubo_lealtad_clientes LIMIT 5;"; Pattern = "Ana Mora|Carlos Rojas|Maria Solis|Jose Vega" },
    @{ Name = "Productos"; Sql = "SELECT product_name, category, ranking_categoria FROM cubo_bestsellers_productos WHERE ranking_categoria <= 5 LIMIT 10;"; Pattern = "Hamburguesa|Pizza|Cafe|Cheesecake|Ensalada" }
)

foreach ($check in $viewChecks) {
    Invoke-Beeline `
        -Title "[8/8] Vista devuelve resultados: $($check.Name)" `
        -JdbcUrl $WarehouseJdbcUrl `
        -Sql $check.Sql `
        -RequiredPatterns @($check.Pattern) | Out-Null
}

Invoke-Beeline `
    -Title "[8/8] Ejecutar validacion HQL completa para evidencia" `
    -JdbcUrl $WarehouseJdbcUrl `
    -File $ValidationFile | Out-Null

Write-Section "Checklist final"
Write-Log "[x] Hive levanta correctamente."
Write-Log "[x] Existe la base de datos del warehouse."
Write-Log "[x] Se crean las dimensiones."
Write-Log "[x] Se crean las tablas de hechos."
Write-Log "[x] Se crean los cubos/vistas OLAP."
Write-Log "[x] Las tablas tienen datos cargados."
Write-Log "[x] Las vistas devuelven resultados."
Write-Log "[x] Hay consultas de prueba/capturas."
Write-Log ""
Write-Log "Resultado: DW validado correctamente."
Write-Log "Evidencia/captura textual: $LogFile"
