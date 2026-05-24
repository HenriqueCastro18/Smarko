@echo off
setlocal
echo ======================================================
echo           Smarko Security - Instalador Final
echo ======================================================

:: 1. Detectar Python
set "PYTHON_CMD="
python --version >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (py --version >nul 2>&1 && set "PYTHON_CMD=py")

:: 2. Criar VENV
if not exist venv (%PYTHON_CMD% -m venv venv)

:: 3. Instalar pacotes corretos
call venv\Scripts\activate
python -m pip install --upgrade pip

echo Instalando bibliotecas necessarias...
:: Instalamos python-dotenv (para o erro do seu log) e bcrypt moderno
pip install python-dotenv bcrypt django sqlparse tzdata asgiref

:: 4. Rodar Migrações
if exist manage.py (
    echo Aplicando configuracoes de banco...
    python manage.py migrate
)

echo ======================================================
echo    Tudo pronto! Agora o erro do 'dotenv' sumiu.
echo    Pode rodar o run.bat.
echo ======================================================
pause