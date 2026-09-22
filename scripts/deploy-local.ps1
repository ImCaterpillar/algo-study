<#
AlgoStudy local one-click runner for Windows PowerShell.

Recommended:
  .\scripts\deploy-local.cmd https://registry.npmmirror.com/

Direct PowerShell usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-local.ps1 -NpmRegistry https://registry.npmmirror.com/ -OpenBrowser
#>
[CmdletBinding()]
param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = '127.0.0.1',
  [string]$FrontendHost = '0.0.0.0',
  [string]$NpmRegistry = 'https://registry.npmjs.org/',
  [switch]$SkipInstall,
  [switch]$OpenBrowser
)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
  Write-Host "[algo-study] $Message"
}

function Assert-Command([string]$Name, [string]$InstallHint) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name was not found. $InstallHint"
  }
}

function Normalize-Registry([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) {
    return 'https://registry.npmjs.org/'
  }
  $trimmed = $Value.Trim()
  if (-not $trimmed.EndsWith('/')) {
    $trimmed = "$trimmed/"
  }
  return $trimmed
}

function New-SecretKey {
  $bytes = New-Object byte[] 48
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  } finally {
    $rng.Dispose()
  }
  return [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_').TrimEnd('=')
}

function Set-EnvValue([string]$Path, [string]$Key, [string]$Value) {
  if (Test-Path $Path) {
    $lines = @(Get-Content -Path $Path)
  } else {
    $lines = @()
  }

  $result = New-Object System.Collections.Generic.List[string]
  $found = $false
  foreach ($line in $lines) {
    if ($line -match ("^" + [regex]::Escape($Key) + "=")) {
      $result.Add("$Key=$Value")
      $found = $true
    } else {
      $result.Add($line)
    }
  }

  if (-not $found) {
    $result.Add("$Key=$Value")
  }
  Set-Content -Path $Path -Value $result -Encoding UTF8
}

function Ensure-BackendEnv {
  $envPath = Join-Path $BackendDir '.env'
  $examplePath = Join-Path $BackendDir '.env.example'
  if (-not (Test-Path $envPath)) {
    Copy-Item -Path $examplePath -Destination $envPath
  }

  $envText = Get-Content -Path $envPath -Raw
  if ($envText -match '(?m)^SECRET_KEY=(replace-with-a-long-random-secret|dev-secret-key-change-me|change-me-before-deploy)\s*$') {
    Set-EnvValue $envPath 'SECRET_KEY' (New-SecretKey)
  }

  $cors = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"
  Set-EnvValue $envPath 'CORS_ORIGINS' $cors
}

function Ensure-FrontendEnv {
  $envPath = Join-Path $FrontendDir '.env'
  $examplePath = Join-Path $FrontendDir '.env.example'
  if (-not (Test-Path $envPath)) {
    Copy-Item -Path $examplePath -Destination $envPath
  }
  Set-EnvValue $envPath 'VITE_API_BASE_URL' "http://${BackendHost}:$BackendPort/api"
}

function Ensure-FrontendNpmrc {
  $npmrcPath = Join-Path $FrontendDir '.npmrc'
  $npmrcContent = @(
    "registry=$NpmRegistry",
    'fund=false',
    'audit=true',
    ''
  )
  Set-Content -Path $npmrcPath -Value $npmrcContent -Encoding UTF8
}

function Test-InternalRegistryResidue {
  $files = @(
    (Join-Path $FrontendDir 'package-lock.json'),
    (Join-Path $FrontendDir '.npmrc'),
    (Join-Path $RootDir '.npmrc')
  )

  foreach ($file in $files) {
    if (Test-Path $file) {
      $text = Get-Content -Path $file -Raw
      if ($text -match 'applied-caas|internal\.api\.openai|artifactory') {
        throw "Private npm registry residue found in $file. Run: .\scripts\fix-npm-registry.cmd $NpmRegistry"
      }
    }
  }
}

function Wait-Backend {
  $url = "http://${BackendHost}:$BackendPort/health"
  Write-Step "Waiting for backend: $url"
  for ($i = 0; $i -lt 60; $i++) {
    try {
      Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null
      Write-Step 'Backend is ready.'
      return
    } catch {
      Start-Sleep -Seconds 1
    }
  }
  throw "Backend health check failed: $url"
}

$NpmRegistry = Normalize-Registry $NpmRegistry
$RootDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BackendDir = Join-Path $RootDir 'backend'
$FrontendDir = Join-Path $RootDir 'frontend'

Assert-Command 'python' 'Please install Python 3.10+ and enable Add python.exe to PATH.'
Assert-Command 'npm' 'Please install Node.js 18+.'

Ensure-BackendEnv
Ensure-FrontendEnv
Ensure-FrontendNpmrc
Test-InternalRegistryResidue

$VenvDir = Join-Path $BackendDir '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
  Write-Step 'Creating Python virtual environment ...'
  & python -m venv $VenvDir
  if ($LASTEXITCODE -ne 0) {
    throw 'Failed to create Python virtual environment.'
  }
}

if (-not $SkipInstall) {
  Write-Step 'Installing backend dependencies ...'
  & $VenvPython -m pip install -r (Join-Path $BackendDir 'requirements.txt')
  if ($LASTEXITCODE -ne 0) {
    throw 'Failed to install backend dependencies.'
  }

  Write-Step "Installing frontend dependencies. npm registry: $NpmRegistry"
  Push-Location $FrontendDir
  try {
    & npm config set registry $NpmRegistry
    if ($LASTEXITCODE -ne 0) { throw 'Failed to set npm registry.' }
    & npm install --registry $NpmRegistry
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install frontend dependencies.' }
  } finally {
    Pop-Location
  }
}

$BackendProcess = $null
try {
  Write-Step 'Starting backend ...'
  $BackendProcess = Start-Process -FilePath $VenvPython `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', $BackendHost, '--port', "$BackendPort") `
    -WorkingDirectory $BackendDir `
    -PassThru

  Wait-Backend

  Write-Host ''
  Write-Host 'AlgoStudy is running locally:'
  Write-Host "  Frontend: http://127.0.0.1:$FrontendPort"
  Write-Host "  Backend:  http://${BackendHost}:$BackendPort"
  Write-Host "  API docs: http://${BackendHost}:$BackendPort/docs"
  Write-Host ''
  Write-Host 'Press Ctrl+C to stop the frontend. Backend will be stopped when this script exits.'

  Push-Location $FrontendDir
  try {
    $env:VITE_API_BASE_URL = "http://${BackendHost}:$BackendPort/api"
    if ($OpenBrowser) {
      & npm run dev -- --host $FrontendHost --port $FrontendPort --open
    } else {
      & npm run dev -- --host $FrontendHost --port $FrontendPort
    }
  } finally {
    Pop-Location
  }
} finally {
  if ($BackendProcess -and -not $BackendProcess.HasExited) {
    Write-Step 'Stopping backend ...'
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
  }
}
