$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$sourceZip = Join-Path $root "release\AI-Web-Browsing-Assistant-source.zip"
$windowsZip = Join-Path $root "release\AI-Web-Browsing-Assistant-windows.zip"
$distRoot = Join-Path $root "dist"

$dirty = git status --porcelain

if ($dirty) {
    throw "The working tree is not clean. Commit source changes before packaging."
}

$trackedSensitive = git ls-files | Where-Object {
    $_ -match '(^|/)\.env($|\.)|\.db$|\.sqlite$|\.key$|\.pem$'
}

if ($trackedSensitive) {
    throw "Sensitive files are tracked by Git:`n$($trackedSensitive -join "`n")"
}

if (-not (Test-Path $distRoot)) {
    throw "The dist directory was not found: $distRoot"
}

$distDirectory = Get-ChildItem $distRoot -Directory | Where-Object {
    Get-ChildItem $_.FullName -Filter "*.exe" -File -ErrorAction SilentlyContinue
} | Select-Object -First 1

if (-not $distDirectory) {
    throw "No packaged EXE directory was found under: $distRoot"
}

$distDir = $distDirectory.FullName

$distSensitive = Get-ChildItem $distDir -Recurse -Force -File | Where-Object {
    $_.Name -match '^\.env$|\.env$|\.db$|\.sqlite$|\.key$|\.pem$'
}

if ($distSensitive) {
    throw "Sensitive files were found in the EXE package:`n$($distSensitive.FullName -join "`n")"
}

New-Item -ItemType Directory -Path (Join-Path $root "release") -Force | Out-Null

git archive --format=zip --output=$sourceZip HEAD

Compress-Archive `
    -Path (Join-Path $distDir "*"), (Join-Path $root "README.md") `
    -DestinationPath $windowsZip `
    -Force

$sourceHash = (Get-FileHash $sourceZip -Algorithm SHA256).Hash
$windowsHash = (Get-FileHash $windowsZip -Algorithm SHA256).Hash

Write-Host ""
Write-Host "Release packages created:"
Write-Host "  $sourceZip"
Write-Host "  SHA256: $sourceHash"
Write-Host "  $windowsZip"
Write-Host "  SHA256: $windowsHash"
