$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$envFile = Join-Path $scriptDir '.env'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -and $_ -notmatch '^\s*#') {
            $parts = $_ -split '='
            if ($parts.Count -ge 2) {
                $name = $parts[0].Trim()
                $value = ($parts[1..] -join '=').Trim()
                Set-Item -Path env:$name -Value $value
            }
        }
    }
}

$logs = Join-Path $scriptDir 'logs'
if (-not (Test-Path $logs)) {
    New-Item -ItemType Directory -Path $logs | Out-Null
}

Write-Host 'Starting dashboard...'
$dashboard = Start-Process -FilePath python -ArgumentList 'app.py' -WorkingDirectory (Join-Path $scriptDir 'dashboard') -RedirectStandardOutput (Join-Path $logs 'dashboard.log') -RedirectStandardError (Join-Path $logs 'dashboard.err') -PassThru
Write-Host "Dashboard PID: $($dashboard.Id)"

Write-Host 'Starting fog processor...'
$fog = Start-Process -FilePath python -ArgumentList 'processor.py' -WorkingDirectory (Join-Path $scriptDir 'fog') -RedirectStandardOutput (Join-Path $logs 'fog.log') -RedirectStandardError (Join-Path $logs 'fog.err') -PassThru
Write-Host "Fog PID: $($fog.Id)"

Write-Host 'Starting simulator...'
$sim = Start-Process -FilePath python -ArgumentList 'publisher.py' -WorkingDirectory (Join-Path $scriptDir 'simulator') -RedirectStandardOutput (Join-Path $logs 'simulator.log') -RedirectStandardError (Join-Path $logs 'simulator.err') -PassThru
Write-Host "Simulator PID: $($sim.Id)"

Write-Host 'All components started.'
Write-Host 'Dashboard: http://localhost:5000'
Write-Host "Logs: $logs\dashboard.log, $logs\fog.log, $logs\simulator.log"