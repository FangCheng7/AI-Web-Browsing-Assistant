$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$sourceZip = Join-Path $root "release\AI-Web-Browsing-Assistant-source.zip"
$windowsZip = Join-Path $root "release\AI-Web-Browsing-Assistant-windows.zip"
$distDir = Join-Path $root "dist\AI网页浏览分析助手"

$dirty = git status --porcelain

if ($dirty) {
    throw "工作区尚未提交。请先提交源码，确保源码压缩包内容可复现。"
}

$trackedSensitive = git ls-files | Where-Object {
    $_ -match '(^|/)\.env($|\.)|\.db$|\.sqlite$|\.key$|\.pem$'
}

if ($trackedSensitive) {
    throw "发现被 Git 跟踪的敏感文件：`n$($trackedSensitive -join "`n")"
}

if (-not (Test-Path $distDir)) {
    throw "找不到 EXE 构建目录：$distDir"
}

$distSensitive = Get-ChildItem $distDir -Recurse -Force -File | Where-Object {
    $_.Name -match '^\.env$|\.env$|\.db$|\.sqlite$|\.key$|\.pem$'
}

if ($distSensitive) {
    throw "EXE 构建目录中发现敏感文件：`n$($distSensitive.FullName -join "`n")"
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
Write-Host "发布包已生成："
Write-Host "  $sourceZip"
Write-Host "  SHA256: $sourceHash"
Write-Host "  $windowsZip"
Write-Host "  SHA256: $windowsHash"
