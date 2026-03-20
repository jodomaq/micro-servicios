/**
 * Página de Login (versión simplificada para desarrollo)
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    Container,
    Paper,
    Typography,
    Button,
    Box,
    Alert,
    CircularProgress,
    TextField,
} from '@mui/material'
import { Login as LoginIcon } from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { useTenant } from '../contexts/TenantContext'

export default function LoginPage() {
    const navigate = useNavigate()
    const { loginDev } = useAuth()
    const { tenant, loading: tenantLoading } = useTenant()
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)
    const [email, setEmail] = useState('admin@demo.com')

    const handleLogin = async (e) => {
        e.preventDefault()
        try {
            setLoading(true)
            setError(null)
            await loginDev(email, 1) // tenant_id = 1 (demo)
            navigate('/dashboard')
        } catch (err) {
            const errorMsg = err.response?.data?.detail || err.message || 'Error al iniciar sesión'
            setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
        } finally {
            setLoading(false)
        }
    }

    if (tenantLoading) {
        return (
            <Box
                display="flex"
                justifyContent="center"
                alignItems="center"
                minHeight="100vh"
            >
                <CircularProgress />
            </Box>
        )
    }

    return (
        <Container component="main" maxWidth="xs">
            <Box
                sx={{
                    minHeight: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                }}
            >
                <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
                    {/* Logo del tenant */}
                    {tenant?.logo_url && (
                        <Box display="flex" justifyContent="center" mb={3}>
                            <img
                                src={tenant.logo_url}
                                alt={tenant.name}
                                style={{ maxHeight: 80, maxWidth: '100%' }}
                            />
                        </Box>
                    )}

                    {/* Título */}
                    <Typography component="h1" variant="h5" align="center" gutterBottom>
                        {tenant?.name || 'Sistema de Comités'}
                    </Typography>

                    <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
                        Inicia sesión para continuar
                    </Typography>

                    {/* Error message */}
                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    {/* Formulario de login */}
                    <Box component="form" onSubmit={handleLogin} sx={{ mt: 3 }}>
                        <TextField
                            fullWidth
                            label="Email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={loading}
                            sx={{ mb: 2 }}
                            required
                        />

                        <Button
                            fullWidth
                            type="submit"
                            variant="contained"
                            startIcon={<LoginIcon />}
                            disabled={loading}
                            sx={{ py: 1.5 }}
                        >
                            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
                        </Button>
                    </Box>

                    {loading && (
                        <Box display="flex" justifyContent="center" mt={3}>
                            <CircularProgress size={24} />
                        </Box>
                    )}

                    {/* Info de desarrollo */}
                    <Alert severity="info" sx={{ mt: 3 }}>
                        <Typography variant="caption" display="block">
                            <strong>Usuarios de prueba:</strong><br />
                            - admin@demo.com (Admin)<br />
                            - superadmin@micro-servicios.com.mx (Super Admin)
                        </Typography>
                    </Alert>
                </Paper>
            </Box>
        </Container>
    )
}
