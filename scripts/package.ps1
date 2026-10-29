$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $root "dist"
$stage = Join-Path $dist "AttendanceHub-source"
$archive = Join-Path $dist "AttendanceHub-source.zip"

if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null

$excludedDirectories = @(".git", "node_modules", ".next", "__pycache__", ".pytest_cache", "dist", "pytest-cache-files-acwa_279", "pytest-cache-files-xdir64uk", "pytest-cache-files-yeruo7t1", "pytest-cache-files-iakmkk2n")
$excludedFiles = @(".env")

Get-ChildItem -LiteralPath $root -Force -File | Where-Object { $_.Name -notin $excludedFiles } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $stage -Force
}

Get-ChildItem -LiteralPath $root -Force -Directory | Where-Object { $_.Name -notin $excludedDirectories } | ForEach-Object {
    $destination = Join-Path $stage $_.Name
    # robocopy accepts directory exclusions at every depth; exit values below 8 are success states.
    & robocopy $_.FullName $destination /E /XD $excludedDirectories /XF $excludedFiles /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Unable to stage $($_.Name) for packaging (robocopy exit code $LASTEXITCODE)." }
}

Get-ChildItem -LiteralPath $stage -Recurse -Force -File | Where-Object {
    $_.Name -eq ".env" -or $_.Extension -in @(".pyc", ".pyo")
} | Remove-Item -Force

Compress-Archive -LiteralPath $stage -DestinationPath $archive -CompressionLevel Optimal
Remove-Item -LiteralPath $stage -Recurse -Force

Write-Host "Package created: $archive"
