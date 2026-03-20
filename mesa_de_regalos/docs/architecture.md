# Arquitectura — Mesa de Regalos

## Visión General

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│   MariaDB    │
│  React+Vite  │     │   FastAPI    │     │              │
│  TailwindCSS │◀────│              │◀────│              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │   Servicios  │
                    │  Externos    │
                    ├──────────────┤
                    │ Mercado Libre│
                    │   (Scraper)  │
                    ├──────────────┤
                    │    PayPal    │
                    │ (Suscripc.) │
                    └──────────────┘
```

## Modelos de Datos
- **User** → Usuarios registrados, con flag `is_premium`
- **GiftTable** → Mesas de regalos (wishlists), con slug público
- **Gift** → Productos individuales con link de afiliado ML

## Flujos Principales
1. Usuario crea mesa de regalos → comparte link público
2. Visitante ve mesa → hace clic en "Comprar" → redirigido a ML con link de afiliado
3. Usuario se suscribe a Premium → PayPal procesa pago → webhook actualiza `is_premium`
