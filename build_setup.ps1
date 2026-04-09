param(
    [string]$PythonExe = "C:\Program Files\PyManager\python.exe",
    [string]$InnoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $PythonExe)) {
    throw "Python nao encontrado em: $PythonExe"
}

if (!(Test-Path $InnoCompiler)) {
    throw "ISCC nao encontrado em: $InnoCompiler"
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
    --workpath "build_irflow_setup" `
    app.py

Copy-Item -Path "database.db" -Destination "release\database.db" -Force
& $InnoCompiler "installer.iss"

Write-Host "Setup pronto em: installer_output\IR FLOW Setup.exe"
Write-Host "Porta padrao do app: 5080"
