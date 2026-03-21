# shared-ui — Sistema de Diseño Compartido

Tokens y componentes CSS comunes para todos los frontends de Micro-Servicios.

## Archivos

| Archivo | Contenido |
|---------|-----------|
| `tokens.css` | Variables CSS (colores, tipografía, espaciado, sombras) |
| `components.css` | Clases reutilizables (navbar, botones, cards, forms, badges) |

## Cómo usar en un frontend React/Vite

### Opción A — Importar directo desde la carpeta del monorepo

En `src/main.jsx` o `src/index.css`:

```js
// Ruta relativa desde el frontend hasta shared-ui/
import '../../shared-ui/tokens.css'
import '../../shared-ui/components.css'
```

### Opción B — Copiar los archivos

Copiar `tokens.css` y `components.css` a `src/assets/` del frontend.

### Google Font (requerida)

Agregar en `index.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
```

---

## Clases disponibles

### Layout
- `.ms-page` — Página base (fondo oscuro, fuente Inter)
- `.ms-container` — Contenedor centrado con max-width
- `.ms-section` — Sección con padding vertical
- `.ms-grid-2/3/4` — Grids responsivos

### Navegación
- `.ms-nav` — Navbar sticky
- `.ms-nav__logo` — Logo con gradiente
- `.ms-nav__links` / `.ms-nav__link` — Links de navegación

### Botones
```html
<button class="ms-btn ms-btn--primary">Guardar</button>
<button class="ms-btn ms-btn--secondary ms-btn--sm">Cancelar</button>
<button class="ms-btn ms-btn--danger ms-btn--lg">Eliminar</button>
<button class="ms-btn ms-btn--ghost">Ver más</button>
```

### Cards
```html
<div class="ms-card">
  <h3 class="ms-card__title">Título</h3>
  <p class="ms-card__body">Descripción</p>
</div>
<div class="ms-card ms-card--glass">...</div>
```

### Formularios
```html
<div class="ms-field">
  <label class="ms-label">Email</label>
  <input class="ms-input" type="email">
  <span class="ms-error-text">Campo requerido</span>
</div>
```

### Badges
```html
<span class="ms-badge ms-badge--primary">Activo</span>
<span class="ms-badge ms-badge--success">Completado</span>
<span class="ms-badge ms-badge--warning">Pendiente</span>
<span class="ms-badge ms-badge--danger">Error</span>
```

### Alertas
```html
<div class="ms-alert ms-alert--info">Información</div>
<div class="ms-alert ms-alert--success">Guardado correctamente</div>
<div class="ms-alert ms-alert--error">Ocurrió un error</div>
```

### Otros
- `<div class="ms-spinner">` — Spinner de carga
- `<hr class="ms-divider">` — Línea divisora
- `<div class="ms-avatar">AB</div>` — Avatar con iniciales

---

## Variables CSS disponibles

Ver `tokens.css` para la lista completa. Prefijo `--ms-*` en todas.

Ejemplos de uso en CSS personalizado:
```css
.mi-componente {
  color: var(--ms-primary);
  background: var(--ms-bg-dark2);
  border-radius: var(--ms-radius-lg);
  font-family: var(--ms-font);
}
```
