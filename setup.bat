@echo off
setlocal enabledelayedexpansion

echo ======================================================
echo    FinHome - Script de Instalacao Automatica
echo ======================================================
echo.

:: 1. Verificar se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no sistema. Por favor, instale o Python antes de continuar.
    pause
    exit /b
)

:: 2. Criar ambiente virtual
echo [+] Criando ambiente virtual (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar o ambiente virtual.
    pause
    exit /b
)

:: 3. Instalar dependencias
echo [+] Instalando dependencias do sistema...
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar as dependencias. Verifique sua conexao com a internet.
    pause
    exit /b
)

:: 4. Preparar Banco de Dados
echo [+] Preparando o Banco de Dados (Migrations)...
.\venv\Scripts\python.exe manage.py makemigrations financas
.\venv\Scripts\python.exe manage.py migrate
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao preparar o banco de dados.
    pause
    exit /b
)

:: 5. Criar Superusuario (Opcional)
echo.
set /p criar_user="Deseja criar um usuario de acesso agora? (S/N): "
if /i "%criar_user%"=="S" (
    echo [+] Siga as instrucoes na tela para criar seu login.
    .\venv\Scripts\python.exe manage.py createsuperuser
)

:: 6. Finalizacao
echo.
echo ======================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo ======================================================
echo.
echo Para rodar o sistema no futuro, use:
echo .\venv\Scripts\python.exe manage.py runserver
echo.
set /p rodar_agora="Deseja iniciar o sistema agora? (S/N): "
if /i "%rodar_agora%"=="S" (
    echo [+] Iniciando servidor...
    start http://127.0.0.1:8000
    .\venv\Scripts\python.exe manage.py runserver
)

pause
