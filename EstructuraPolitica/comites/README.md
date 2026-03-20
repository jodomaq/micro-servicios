# Frontend - Comités

Frontend React 18 con Material-UI para el sistema de gestión de comités.

## 🚀 Inicio Rápido

```powershell
cd comites

# Copiar variables de entorno
copy .env.example .env

# Editar .env con tus configuraciones
notepad .env

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

La aplicación estará disponible en: **http://localhost:5173**

---

## 📋 Configuración (.env)

Edita `.env` con las siguientes variables:

```env
# URL del API backend
VITE_API_URL=http://localhost:8000

# ID del tenant (para desarrollo)
VITE_TENANT_ID=1

# OAuth Credentials
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
VITE_MICROSOFT_CLIENT_ID=your_microsoft_client_id
```

---

## 🏗️ Estructura del Proyecto

```
comites/
├── src/
│   ├── components/
│   │   ├── Layout.jsx              # Layout principal con navegación
│   │   └── TenantThemeProvider.jsx # Tema dinámico por tenant
│   ├── contexts/
│   │   ├── AuthContext.jsx         # Autenticación OAuth
│   │   └── TenantContext.jsx       # Multi-tenancy
│   ├── pages/
│   │   ├── LoginPage.jsx           # Login OAuth
│   │   ├── DashboardPage.jsx       # Dashboard principal
│   │   ├── CommitteesPage.jsx      # Gestión de comités
│   │   ├── HierarchyPage.jsx       # Vista jerárquica
│   │   └── AdminDashboard.jsx      # Panel de administración
│   ├── services/
│   │   └── api.js                  # Cliente Axios configurado
│   ├── config.js                   # Configuración de la app
│   ├── App.jsx                     # Componente principal
│   └── main.jsx                    # Entry point
├── package.json
├── vite.config.js
└── .env
```

---

## 🎨 Características

### Multi-Tenancy
- Detección automática de tenant por subdominio
- Tema dinámico con colores del tenant
- Logo personalizado en AppBar

### Autenticación
- Login con Google OAuth
- Login con Microsoft OAuth
- Protección de rutas
- Manejo de sesiones

### Diseño Responsive
- Mobile-first con Material-UI
- Menú hamburguesa en móviles
- Drawer navegación
- AppBar sticky

### Admin Dashboard
- Gestión de coordinadores
- Asignación de jerarquías
- Eliminación de comités

---

## 📦 Dependencias Principales

- **React 18** - Framework frontend
- **Material-UI v6** - Componentes UI
- **React Router v6** - Navegación
- **Axios** - Cliente HTTP
- **@react-oauth/google** - Google OAuth
- **@azure/msal-react** - Microsoft OAuth
- **React Hook Form** - Formularios
- **Yup** - Validación

---

## 🔧 Scripts Disponibles

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Lint
npm run lint
```

---

## 🚦 Estado Actual

### ✅ Completado

- Setup de proyecto con Vite
- Configuración de Material-UI
- TenantContext  y tema dinámico
- AuthContext con OAuth
- Layout responsive
- Login page
- Rutas protegidas
- Dashboard básico
- AdminDashboard estructura

### 🔜 Pendiente

- Componentes de comités (form, list, explorer)
- Componentes de miembros
- Upload de documentos
- Vista de árbol jerárquico completa
- Gestión completa en AdminDashboard
- Formularios con validación
- Integración completa con API

---

## 📝 Próximos Pasos

1. **Implementar servicios del API**
   - committeeService.js
   - userService.js
   - hierarchyService.js

2. **Componentes de comités**
   - CommitteeForm
   - CommitteeList
   - CommitteeMemberForm

3. **AdminDashboard completo**
   - Tabla de coordinadores
   - Formulario de asignación
   - Gestión de eliminaciones

---

## 🐛 Troubleshooting

### Error: Cannot find module
```bash
# Reinstalar dependencias
rm -rf node_modules
npm install
```

### El API no responde
- Verificar que el backend esté corriendo en puerto 8000
- Verificar VITE_API_URL en .env
- Revisar headers en network tab (debe incluir X-Tenant-ID)

### OAuth no funciona
- Verificar credenciales en .env
- Configurar URLs autorizadas en Google/Microsoft console
- Agregar http://localhost:5173 como redirect URI

---

¡Frontend listo para desarrollo! 🎉
