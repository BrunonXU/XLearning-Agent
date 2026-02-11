# XLearning-Agent - 一键启动 UI
# 无需手动激活 venv，直接使用 venv 内的 Python 运行 Streamlit
# 用法: .\scripts\run_ui.ps1  或  cd scripts; .\run_ui.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.FullName
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "错误: 未找到 venv，请先执行 python -m venv venv" -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot
Write-Host "启动 XLearning-Agent UI..." -ForegroundColor Green
& $VenvPython -m streamlit run app.py @args
