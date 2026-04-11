param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

if (-not $PythonExe) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $pythonCommand) {
        throw "Python nao encontrado no PATH"
    }
    $PythonExe = $pythonCommand.Source
}

if (!(Get-Command $PythonExe -ErrorAction SilentlyContinue) -and !(Test-Path $PythonExe)) {
    throw "Python nao encontrado em: $PythonExe"
}

if (!(Test-Path "assets\ir_flow.ico")) {
    throw "Icone nao encontrado em assets\ir_flow.ico"
}

if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm nao encontrado no PATH"
}

Push-Location "frontend"
try {
    if (!(Test-Path "node_modules")) {
        npm install
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar dependencias do frontend"
        }
    }

    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar frontend\\dist"
    }
}
finally {
    Pop-Location
}

& $PythonExe -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name "IR FLOW" `
    --icon "assets\ir_flow.ico" `
    --add-data "data;data" `
    --add-data "frontend\dist;frontend\dist" `
    --distpath "release" `
    --workpath "build_irflow2" `
    app.py

Copy-Item -Path "database.db" -Destination "release\database.db" -Force

Write-Host "Build concluido em: release\IR FLOW.exe"
Write-Host "Porta padrao do app: 5080"
