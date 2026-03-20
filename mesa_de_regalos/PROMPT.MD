### Copia y pega el siguiente texto en tu IA:

**Actúa como un Senior Full-Stack Developer y UX/UI Designer** experto en Python (FastAPI), React.js (Vite + TailwindCSS) y MariaDB. Vamos a construir el MVP de una aplicación web diseñada para monetizar mediante el programa de afiliados de Mercado Libre y suscripciones premium procesadas con **PayPal**.

**Contexto de Marca y Localización (MUY IMPORTANTE):**
- **Nombre de la App:** "Mesa de Regalos" (con el subtítulo sutil: *tu wishlist digital*).
- **Idioma y Público:** 100% en español, adaptado específicamente para el público de México y Latinoamérica. Todo el copy de la interfaz, alertas y correos debe sonar natural para un usuario mexicano (ej. "Añadir a mi mesa", "Marcar como comprado", "Copiar enlace").
- **Dominio de Producción:** El sistema vivirá en `https://micro-servicios.com.mx`.
- **Diseño (UI/UX):** El diseño debe ser muy llamativo, visual y fácil de usar para cualquier persona (incluso tías o abuelas que entren a ver qué regalar). Debe usar TailwindCSS con tarjetas (cards) grandes para las fotos de los regalos, botones de "Comprar" con colores de alta conversión y una interfaz limpia pensada primero para celulares (Mobile-First).

Como estamos desarrollando con asistencia de IA, el proyecto debe seguir estrictamente la arquitectura orientada a agentes, implementando contexto, runbooks y scripts.

Por favor, ayúdame a inicializar el proyecto cumpliendo estas 5 especificaciones:

**1. Estructura de Directorios (Orientada a IA)**
Crea la siguiente estructura exacta:
```text
mesa-de-regalos-app/
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
│       └── services/     # scraper.py y paypal_service.py
└── frontend/
    ├── package.json
    └── src/
```

**2. Archivos de Configuración y Contexto IA**
- Escribe el `.gitignore` y un `.env.example` que incluya: `DATABASE_URL`, credenciales de Mercado Libre (`ML_CAMP_ID`), credenciales de PayPal (`PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`, `PAYPAL_MODE`) y el dominio base `FRONTEND_URL=https://micro-servicios.com.mx`.
- Escribe el archivo `CLAUDE.md` (o `CURSOR.md`) instruyendo a la IA que, de ahora en adelante, *todo el frontend, respuestas de API y mensajes de error deben estar en español*, que el diseño debe ser moderno/visual usando Tailwind, y recordando el propósito del negocio.

**3. Base de Datos (MariaDB)**
Genera los modelos de SQLAlchemy en `backend/app/models/` para:
- `User`: id, email, password_hash, **is_premium** (boolean), **paypal_subscription_id**.
- `GiftTable` (en lugar de Wishlist): id, user_id, title, is_public, slug_url.
- `Gift` (en lugar de Item): id, gift_table_id, original_url, **affiliate_url**, image_url, title, price, status ('disponible', 'comprado').

**4. Lógica del Scraper y Afiliados (Mercado Libre)**
En `backend/app/services/scraper.py`, crea una función asíncrona (`httpx` y `BeautifulSoup`) que:
- Reciba una URL cruda de Mercado Libre México.
- Extraiga `og:title`, `og:image` y el precio del HTML.
- Convierta la URL original a un **link de afiliado**. Transforma la URL aplicando *URL encoding* e inyéctala en el formato de redirección de ML junto con la variable `ML_CAMP_ID` del `.env`.

**5. Lógica de Suscripciones (PayPal)**
En `backend/app/services/paypal_service.py`, implementa la integración con la API REST de PayPal:
- Una función para generar el Access Token.
- Una función `create_subscription_link(user_id)` que interactúe con la API de Subscriptions de PayPal para devolver la URL de pago, enviando al usuario de regreso a `https://micro-servicios.com.mx/exito` al terminar.
- Un bosquejo para procesar el Webhook de PayPal que actualizará `is_premium = True` en la base de datos.

**Instrucción de salida:**
Para esta primera respuesta, entrégame **únicamente**:
1. El contenido del `CLAUDE.md` y `.env.example`.
2. El código de `backend/app/models/` (Base de datos con nombres ajustados al dominio del problema).
3. El código de `backend/app/services/scraper.py` (Lógica de Mercado Libre).
4. El código de `backend/app/services/paypal_service.py` (Lógica de PayPal).

https://mywishlist.online/