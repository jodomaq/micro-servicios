/**
 * Cliente API con interceptores para autenticación y tenant
 */
import axios from 'axios'
import config from '../config'

const api = axios.create({
    baseURL: `${config.apiUrl}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Interceptor de request - agregar token y tenant_id
api.interceptors.request.use(
    (config) => {
        // Agregar token si existe
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }

        // Agregar tenant_id
        const tenantId = localStorage.getItem('tenant_id') || import.meta.env.VITE_TENANT_ID
        if (tenantId) {
            config.headers['X-Tenant-ID'] = tenantId
        }

        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Interceptor de response - manejar errores
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            // Token expirado o inválido
            if (error.response.status === 401) {
                localStorage.removeItem('access_token')
                localStorage.removeItem('user')
                window.location.href = '/login'
            }

            // Tenant suspendido o sin acceso
            if (error.response.status === 403) {
                console.error('Acceso denegado:', error.response.data.detail)
            }
        }

        return Promise.reject(error)
    }
)

export default api
