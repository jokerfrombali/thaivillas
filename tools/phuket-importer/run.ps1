# Starts Phuket Importer in Docker. Run from anywhere: .\run.ps1
$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here "..\..")).Path
Set-Location $Here
docker build -t thaivillas-phuket-importer .
Write-Host "Open http://localhost:8093  (results -> $Repo\imports)"
docker run --rm --name thaivillas-phuket-importer -p 8093:8090 `
  -e "THAIVILLAS_HOST_WORKSPACE=$Repo" `
  -v "${Repo}:/workspace" thaivillas-phuket-importer
