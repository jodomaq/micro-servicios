
## Repository Overview
1. Monorepo con múltiples SaaS independientes. Todos los backends están **fusionados en `backend_micro/`** como un solo servidor FastAPI y Mariadb. Los frontends son apps React+Vite independientes que apuntan al mismo backend.
2. Los frontend deben estar en carpetas separadas
3. El backend debe estar todo en una carpeta para que pueda retomar las mismas keys de .env, como por ejemplo la de paypal para cobrar los SaaS
4. El url del sitio es micro-servicios.com.mx
5. Debe haber una landing page inicial que redirija a los SaaS, cada SaaS debe tener su propia ruta o url por ejemplo https://micro-servicios.com.mx/Saas1, https://micro-servicios.com.mx/Saas2, https://micro-servicios.com.mx/Saas3 ... https://micro-servicios.com.mx/SaasN


## Landing Page
Crear una Landing Page usando el skill /frontend-design, con estilos, usando colores, estilos y efectos parecidos a la siguiente página: https://techy-xi.vercel.app/?storefront=envato-elements 
La página tiene el objetivo de mostrar algunos servicios web, los cuales deberan tener una tarjeta de acceso, así como también ser parte de los menús.
Genera descripciones para cada micro-servicio, la idea es venderlos por medio de publicidad CEO, usa palabras y estilos que promuevan esas características.
Agrega imágenes relacionadas desde catálogos de imagenes gratuitas en la web
Escribe la página en español.
Estos son los micro-servicios:
1. IQTest
2. Convertir tablas a Excel
3. Historia clínica con IA
4. Reparación de fotografías antiguas con IA
5. Quinielas entra amigos
6. Cuestionarios para alumnos en clase
7. Generador de QR
8. Generador de QR de menú, subir menú
9. Test de orientación vocacional
10. Lectura de Tarot
11. Acortador de enlace
12. Te digo tu futuro
13. De imagen a diagrama en powerpoint
14. Desarrollo de Landing Page
15. Generación de Curriculum
16. Estructura Política
17. Mesa de Regalos

## Puntualizaciones
Genera todos los archivos adicionales del código: .gitignore .env requirements.txt 

## Crea una estructura de Directorios (Orientada a IA)**
```text
micro-servicios-app/
├── .env                  
├── .gitignore            
├── CLAUDE.md             # Reglas base de IA, stack, dominio e idioma
├── docs/                 
│   ├── architecture.md
│   ├── decisions/        
│   └── runbooks/         
├── tools/
│   └── scripts/          
├── backend/
│   ├── requirements.txt  # FastAPI, httpx, bs4, sqlalchemy, paypalrestsdk, etc.
│   ├── main.py
│   └── app/
│       ├── core/         
│       ├── models/       
│       ├── routers/      
│       └── services/     # paypal_service.py
└── frontend/
    ├── package.json
    └── src/
```

