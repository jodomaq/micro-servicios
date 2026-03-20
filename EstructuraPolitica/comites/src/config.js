/**
 * Configuración de la aplicación frontend
 */

const config = {
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    tenantId: import.meta.env.VITE_TENANT_ID || '1',
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    microsoftClientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || '',
    baseDomain: import.meta.env.VITE_BASE_DOMAIN || 'micro-servicios.com.mx',
}

export default config
