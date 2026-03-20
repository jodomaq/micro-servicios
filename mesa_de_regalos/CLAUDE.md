# Mesa de Regalos — Contexto para IA

## Identidad del Proyecto
- **Nombre:** Mesa de Regalos (*tu wishlist digital*)
- **Dominio de producción:** `https://micro-servicios.com.mx`
- **Propósito:** Aplicación web para crear mesas de regalos (wishlists) con productos de Mercado Libre México. Monetización dual:
  1. **Programa de afiliados de Mercado Libre:** cada enlace de producto se convierte en un link de afiliado que genera comisión por venta.
  2. **Suscripciones Premium vía PayPal:** funcionalidades avanzadas desbloqueadas con pago recurrente.

## Stack Técnico
| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy |
| Base de datos | MariaDB |
| Frontend | React 18 · Vite · TailwindCSS |
| Pagos | PayPal REST API (Subscriptions) |
| Scraping | httpx + BeautifulSoup4 |

## Reglas Obligatorias

### 1. Idioma — Español (MX) siempre
- **Todo** el frontend (labels, botones, placeholders, tooltips) debe estar en español natural para México.
- **Todas** las respuestas de la API (mensajes de éxito, errores, validaciones) deben estar en español.
- Ejemplos de copy correcto: "Añadir a mi mesa", "Marcar como comprado", "Copiar enlace", "Iniciar sesión", "Tu mesa se creó con éxito".
- **Nunca** mezclar inglés en la interfaz de usuario.

### 2. Diseño — Mobile-First, Visual, Alta Conversión
- Diseño pensado **primero para celulares** y luego adaptado a escritorio.
- Usar **tarjetas (cards) grandes** con fotos de productos como protagonistas.
- Botones de "Comprar" con **colores de alta conversión** (verde, naranja o amarillo llamativo).
- La interfaz debe ser tan sencilla que cualquier persona pueda usarla sin instrucciones.
- Paleta de colores consistente, tipografía legible, espaciado generoso.
- TailwindCSS como framework de estilos; no usar CSS custom salvo excepciones justificadas.

### 3. Arquitectura
- Backend organizado en: `core/` (config, DB), `models/`, `routers/`, `services/`.
- Nombres de modelos en el dominio del problema: `GiftTable` (no Wishlist), `Gift` (no Item).
- Variables de entorno centralizadas en `.env`, cargadas con `pydantic-settings`.
- Los endpoints de la API deben usar prefijo `/api/v1/`.

### 4. Seguridad
- Nunca exponer credenciales en código; siempre usar variables de entorno.
- Validar URLs del scraper contra un whitelist de dominios permitidos (mercadolibre.com.mx).
- Hashear contraseñas con bcrypt.
- Tokens JWT para autenticación.

### 5. Convenciones de Código
- Código Python: snake_case, type hints, docstrings en español.
- Código React: componentes funcionales, hooks, nombres de componentes en PascalCase.
- Commits descriptivos en español.
