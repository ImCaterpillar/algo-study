<#
Fix npm registry settings and remove private registry residue from package-lock.json.

Recommended from Windows CMD/PowerShell:
  .\scripts\fix-npm-registry.cmd https://registry.npmmirror.com/

Direct PowerShell usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\fix-npm-registry.ps1 -Registry https://registry.npmmirror.com/
#>
[CmdletBinding()]
param(
  [string]$Registry = 'https://registry.npmjs.org/',
  [switch]$RemoveNodeModules,
  [switch]$RemoveLockFile
)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
  Write-Host "[algo-study] $Message"
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

$Registry = Normalize-Registry $Registry
$RootDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$FrontendDir = Join-Path $RootDir 'frontend'
$LockPath = Join-Path $FrontendDir 'package-lock.json'
$NpmrcPath = Join-Path $FrontendDir '.npmrc'

if (-not (Test-Path $FrontendDir)) {
  throw "frontend directory not found: $FrontendDir"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  throw 'npm was not found. Please install Node.js 18+ and reopen the terminal.'
}

Write-Step "Setting npm registry: $Registry"
& npm config set registry $Registry
if ($LASTEXITCODE -ne 0) {
  throw 'npm config set registry failed.'
}

$npmrcContent = @(
  "registry=$Registry",
  'fund=false',
  'audit=true',
  ''
)
Set-Content -Path $NpmrcPath -Value $npmrcContent -Encoding UTF8
Write-Step "Wrote $NpmrcPath"

if ($RemoveNodeModules) {
  $nodeModules = Join-Path $FrontendDir 'node_modules'
  if (Test-Path $nodeModules) {
    Write-Step 'Removing frontend node_modules ...'
    Remove-Item -Recurse -Force $nodeModules
  }
}

if ($RemoveLockFile) {
  if (Test-Path $LockPath) {
    Write-Step 'Removing frontend package-lock.json. npm install will regenerate it.'
    Remove-Item -Force $LockPath
  }
} elseif (Test-Path $LockPath) {
  Write-Step 'Checking frontend package-lock.json registry URLs ...'
  $text = Get-Content -Path $LockPath -Raw
  $text = $text -replace 'https://packages\.applied-caas-gateway1\.internal\.api\.openai\.org/artifactory/api/npm/npm-public/', $Registry
  $text = $text -replace 'https://[^"\s]+/artifactory/api/npm/npm-public/', $Registry
  Set-Content -Path $LockPath -Value $text -Encoding UTF8
}

Write-Step 'Done.'
Write-Host "Next command: .\\start-windows.cmd $Registry"
