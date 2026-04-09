param(
    [string]$PythonExe = "C:\Program Files\PyManager\python.exe"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $PythonExe)) {
    throw "Python nao encontrado em: $PythonExe"
}

if (!(Test-Path "assets\ir_flow.ico")) {
    throw "Icone nao encontrado em assets\ir_flow.ico"
}

& $PythonExe -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name "IR FLOW" `
    --icon "assets\ir_flow.ico" `
    --add-data "templates;templates" `
    --add-data "data;data" `
    --distpath "release" `
    --workpath "build_irflow2" `
    app.py

Copy-Item -Path "database.db" -Destination "release\database.db" -Force

Write-Host "Build concluido em: release\IR FLOW.exe"
Write-Host "Porta padrao do app: 5080"
