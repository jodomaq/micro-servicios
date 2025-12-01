@echo off
REM Script de inicialización del sistema de pagos y suscripciones
REM Excel Converter - Micro Servicios

echo ======================================
echo Excel Converter - Setup Inicial
echo ======================================
echo.

REM Verificar Python
echo 1. Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado. Instala Python 3.8 o superior.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python encontrado: %PYTHON_VERSION%

REM Verificar Node.js
echo.
echo 2. Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js no esta instalado. Instala Node.js 18 o superior.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js encontrado: %NODE_VERSION%

REM Verificar npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm no esta instalado.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [OK] npm encontrado: %NPM_VERSION%

REM Configurar Backend
echo.
echo 3. Configurando Backend...
cd backend_micro
if errorlevel 1 (
    echo [ERROR] No se encontro el directorio backend_micro
    pause
    exit /b 1
)

REM Verificar si existe .env
if not exist .env (
    echo [AVISO] No existe archivo .env en backend
    echo    Copiando desde .env.example...
    copy .env.example .env
    echo [AVISO] Por favor, edita backend_micro\.env con tus credenciales
    pause
)

REM Crear entorno virtual si no existe
if not exist venv (
    echo    Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
)

REM Activar entorno virtual
echo    Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual
    pause
    exit /b 1
)

REM Instalar dependencias
echo    Instalando dependencias de Python...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias de Python
    pause
    exit /b 1
)
echo [OK] Dependencias de Python instaladas

REM Inicializar base de datos
echo    Inicializando base de datos...
python init_db.py
if errorlevel 1 (
    echo [AVISO] Error al inicializar la base de datos (continuando...)
)

cd ..

REM Configurar Frontend
echo.
echo 4. Configurando Frontend...
cd ExcelConverter
if errorlevel 1 (
    echo [ERROR] No se encontro el directorio ExcelConverter
    pause
    exit /b 1
)

REM Verificar si existe .env
if not exist .env (
    echo [AVISO] No existe archivo .env en frontend
    echo    Copiando desde .env.example...
    copy .env.example .env
    echo [AVISO] Por favor, edita ExcelConverter\.env con tus credenciales
    pause
)

REM Instalar dependencias
echo    Instalando dependencias de Node.js...
call npm install
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias de Node.js
    pause
    exit /b 1
)
echo [OK] Dependencias de Node.js instaladas

cd ..

REM Resumen
echo.
echo ======================================
echo Setup Completado
echo ======================================
echo.
echo Para iniciar el sistema:
echo.
echo Backend (terminal 1):
echo   cd backend_micro
echo   venv\Scripts\activate
echo   uvicorn main:app --reload --port 8000
echo.
echo Frontend (terminal 2):
echo   cd ExcelConverter
echo   npm run dev
echo.
echo Luego abre: http://localhost:5173
echo.
echo ======================================
echo Configuracion Requerida:
echo ======================================
echo.
echo 1. Google OAuth:
echo    - Obten Client ID en: https://console.cloud.google.com/
echo    - Configura en backend\.env y ExcelConverter\.env
echo.
echo 2. PayPal:
echo    - Obten credenciales en: https://developer.paypal.com/
echo    - Configura en backend\.env
echo.
echo 3. OpenAI:
echo    - Obten API key en: https://platform.openai.com/
echo    - Configura en backend\.env
echo.
echo Consulta README.md para mas informacion
echo.
pause
