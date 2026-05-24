@echo off
echo ======================================================
echo           Smarko Security - Iniciando Servidor
echo ======================================================

:: 1. Ativa o ambiente virtual
if exist venv (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate
) else (
    echo [ERRO] Ambiente virtual nao encontrado! 
    echo Por favor, rode o 'install.bat' primeiro.
    pause
    exit
)

:: 2. Abre o navegador automaticamente
:: Mudamos para a porta 8001 para evitar o erro de cache HTTPS na porta 8000
echo Abrindo o navegador em http://127.0.0.1:8001/
start http://127.0.0.1:8001/

:: 3. Inicia o servidor do Django na porta 8001
echo Iniciando o Django na porta 8001...
python manage.py runserver 8001

pause