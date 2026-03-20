/**
 * Context para gestión de tenant (multi-tenancy)
 * Detecta tenant por subdominio, fallback a configuración
 */
import { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'
import config from '../config'

const TenantContext = createContext()

export const TenantProvider = ({ children }) => {
    const [tenant, setTenant] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        loadTenant()
    }, [])

    const loadTenant = async () => {
        try {
            setLoading(true)
            let tenantId = config.tenantId

            // Detectar subdominio (ej: partido1.micro-servicios.com.mx)
            const hostname = window.location.hostname
            const baseDomain = config.baseDomain
            if (baseDomain && hostname.endsWith(baseDomain) && hostname !== baseDomain && !hostname.startsWith('www.')) {
                const subdomain = hostname.replace(`.${baseDomain}`, '')
                if (subdomain && subdomain !== 'localhost') {
                    try {
                        const subRes = await api.get(`/public/tenant/by-subdomain/${subdomain}`)
                        if (subRes.data?.id) {
                            tenantId = subRes.data.id
                        }
                    } catch {
                        console.warn(`Subdomain "${subdomain}" not found, using default tenant`)
                    }
                }
            }

            localStorage.setItem('tenant_id', tenantId)

            const response = await api.get('/auth/tenant')
            setTenant(response.data)
        } catch (err) {
            console.error('Error loading tenant:', err)
            setError(err.response?.data?.detail || 'Error al cargar configuración')
        } finally {
            setLoading(false)
        }
    }

    const value = {
        tenant,
        loading,
        error,
        reloadTenant: loadTenant,
    }

    return (
        <TenantContext.Provider value={value}>
            {children}
        </TenantContext.Provider>
    )
}

export const useTenant = () => {
    const context = useContext(TenantContext)
    if (!context) {
        throw new Error('useTenant must be used within TenantProvider')
    }
    return context
}
