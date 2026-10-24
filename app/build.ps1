# Baut "G1R Mod Atlas.exe" nach app\dist\
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
Set-Location $root
$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
    python -m venv .venv
    & $py -m pip install --disable-pip-version-check pywebview pyinstaller pillow
}
& $py app\make_icon.py
& $py -m PyInstaller --noconfirm --onefile --windowed `
    --name 'G1R Mod Atlas' `
    --icon (Join-Path $root 'app\icon.ico') `
    --add-data ((Join-Path $root 'docs') + ';docs') `
    --distpath (Join-Path $root 'app\dist') --workpath (Join-Path $root 'app\build') --specpath (Join-Path $root 'app\build') `
    (Join-Path $root 'app\main.py')
if ($LASTEXITCODE -ne 0) { throw "PyInstaller ist fehlgeschlagen ($LASTEXITCODE)" }
Write-Output "Fertig: app\dist\G1R Mod Atlas.exe"
