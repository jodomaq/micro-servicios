#!/bin/bash

# Script de inicialización del sistema de pagos y suscripciones
# Excel Converter - Micro Servicios

echo "======================================"
echo "Excel Converter - Setup Inicial"
echo "======================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para mostrar errores
error() {
    echo -e "${RED}❌ Error: $1${NC}"
    exit 1
}

# Función para mostrar avisos
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Función para mostrar éxitos
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Verificar Python
echo "1. Verificando Python..."
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        error "Python no está instalado. Instala Python 3.8 o superior."
    fi
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi
success "Python encontrado: $($PYTHON_CMD --version)"

# Verificar Node.js
echo ""
echo "2. Verificando Node.js..."
if ! command -v node &> /dev/null; then
    error "Node.js no está instalado. Instala Node.js 18 o superior."
fi
success "Node.js encontrado: $(node --version)"

# Verificar npm
if ! command -v npm &> /dev/null; then
    error "npm no está instalado."
fi
success "npm encontrado: $(npm --version)"

# Configurar Backend
echo ""
echo "3. Configurando Backend..."
cd backend_micro || error "No se encontró el directorio backend_micro"

# Verificar si existe .env
if [ ! -f .env ]; then
    warning "No existe archivo .env en backend"
    echo "   Copiando desde .env.example..."
    cp .env.example .env || error "No se pudo copiar .env.example"
    warning "   Por favor, edita backend_micro/.env con tus credenciales antes de continuar"
    read -p "   Presiona Enter cuando hayas configurado el archivo .env..."
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "   Creando entorno virtual..."
    $PYTHON_CMD -m venv venv || error "No se pudo crear el entorno virtual"
    success "Entorno virtual creado"
fi

# Activar entorno virtual
echo "   Activando entorno virtual..."
source venv/bin/activate || source venv/Scripts/activate || error "No se pudo activar el entorno virtual"

# Instalar dependencias
echo "   Instalando dependencias de Python..."
pip install -r requirements.txt || error "No se pudieron instalar las dependencias de Python"
success "Dependencias de Python instaladas"

# Inicializar base de datos
echo "   Inicializando base de datos..."
$PYTHON_CMD init_db.py || warning "Error al inicializar la base de datos (continuando...)"

cd ..

# Configurar Frontend
echo ""
echo "4. Configurando Frontend..."
cd ExcelConverter || error "No se encontró el directorio ExcelConverter"

# Verificar si existe .env
if [ ! -f .env ]; then
    warning "No existe archivo .env en frontend"
    echo "   Copiando desde .env.example..."
    cp .env.example .env || error "No se pudo copiar .env.example"
    warning "   Por favor, edita ExcelConverter/.env con tus credenciales"
    read -p "   Presiona Enter cuando hayas configurado el archivo .env..."
fi

# Instalar dependencias
echo "   Instalando dependencias de Node.js..."
npm install || error "No se pudieron instalar las dependencias de Node.js"
success "Dependencias de Node.js instaladas"

cd ..

# Resumen
echo ""
echo "======================================"
echo "✨ Setup Completado"
echo "======================================"
echo ""
echo "Para iniciar el sistema:"
echo ""
echo "Backend (terminal 1):"
echo "  cd backend_micro"
echo "  source venv/bin/activate  # o venv\\Scripts\\activate en Windows"
echo "  uvicorn main:app --reload --port 8000"
echo ""
echo "Frontend (terminal 2):"
echo "  cd ExcelConverter"
echo "  npm run dev"
echo ""
echo "Luego abre: http://localhost:5173"
echo ""
echo "======================================"
echo "Configuración Requerida:"
echo "======================================"
echo ""
echo "1. Google OAuth:"
echo "   - Obtén Client ID en: https://console.cloud.google.com/"
echo "   - Configura en backend/.env y ExcelConverter/.env"
echo ""
echo "2. PayPal:"
echo "   - Obtén credenciales en: https://developer.paypal.com/"
echo "   - Configura en backend/.env"
echo ""
echo "3. OpenAI:"
echo "   - Obtén API key en: https://platform.openai.com/"
echo "   - Configura en backend/.env"
echo ""
echo "Consulta README.md para más información"
echo ""
