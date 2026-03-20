/**
 * Context para autenticación (OAuth deshabilitado, login simple para desarrollo)
 */
import { createContext, useContext, useState, useEffect } from 'react'
// OAuth comentado para desarrollo
// import { useGoogleLogin } from '@react-oauth/google'
// import { useMsal } from '@azure/msal-react'
import api from '../services/api'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    // const { instance: msalInstance } = useMsal()

    useEffect(() => {
        // Verificar si hay sesión guardada
        const savedToken = localStorage.getItem('access_token')
        const savedUser = localStorage.getItem('user')

        if (savedToken && savedUser) {
            setUser(JSON.parse(savedUser))
            // fetchCurrentUser() // Comentado para desarrollo
        }

        setLoading(false)
    }, [])

    const fetchCurrentUser = async () => {
        try {
            const response = await api.get('/auth/me')
            setUser(response.data)
            localStorage.setItem('user', JSON.stringify(response.data))
        } catch (error) {
            console.error('Error fetching current user:', error)
            logout()
        }
    }

    // Login simple para desarrollo
    const loginDev = async (email, tenant_id = 1) => {
        try {
            setLoading(true)

            const response = await api.post('/auth/dev-login', {
                email,
                tenant_id
            })

            const { access_token, user: userData, tenant } = response.data

            // Guardar token y usuario
            localStorage.setItem('access_token', access_token)
            localStorage.setItem('user', JSON.stringify(userData))
            localStorage.setItem('tenant_id', tenant.id.toString())

            setUser(userData)

            return userData
        } catch (error) {
            console.error('Error en login dev:', error)
            throw error
        } finally {
            setLoading(false)
        }
    }

    // OAuth comentado para desarrollo
    /*
    const loginWithGoogle = async (tokenResponse) => {
        try {
            setLoading(true)

            const response = await api.post('/auth/google', {
                token: tokenResponse.credential,
                consent_privacy_policy: true,
                consent_terms: true,
            })

            const { access_token, user: userData, tenant } = response.data

            // Guardar token y usuario
            localStorage.setItem('access_token', access_token)
            localStorage.setItem('user', JSON.stringify(userData))
            localStorage.setItem('tenant_id', tenant.id.toString())

            setUser(userData)

            return userData
        } catch (error) {
            console.error('Error en login con Google:', error)
            throw error
        } finally {
            setLoading(false)
        }
    }

    const loginWithMicrosoft = async () => {
        try {
            setLoading(true)

            // Solicitar login con Microsoft
            const loginResponse = await msalInstance.loginPopup({
                scopes: ['User.Read'],
            })

            const response = await api.post('/auth/microsoft', {
                access_token: loginResponse.accessToken,
                consent_privacy_policy: true,
                consent_terms: true,
            })

            const { access_token, user: userData, tenant } = response.data

            // Guardar token y usuario
            localStorage.setItem('access_token', access_token)
            localStorage.setItem('user', JSON.stringify(userData))
            localStorage.setItem('tenant_id', tenant.id.toString())

            setUser(userData)

            return userData
        } catch (error) {
            console.error('Error en login con Microsoft:', error)
            throw error
        } finally {
            setLoading(false)
        }
    }
    */

    const logout = () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        setUser(null)

        // Logout de Microsoft si está activo (comentado)
        // if (msalInstance.getActiveAccount()) {
        //     msalInstance.logout()
        // }
    }

    const value = {
        user,
        loading,
        isAuthenticated: !!user,
        isAdmin: user?.is_tenant_admin || user?.is_super_admin,
        isSuperAdmin: user?.is_super_admin,
        loginDev, // Login simple para desarrollo
        // loginWithGoogle, // Comentado
        // loginWithMicrosoft, // Comentado
        logout,
        refreshUser: fetchCurrentUser,
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
