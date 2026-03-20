/**
 * Componente principal de la aplicación
 * Configura rutas, contexts y providers
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { TenantProvider } from './contexts/TenantContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { TenantThemeProvider } from './components/TenantThemeProvider'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CommitteesPage from './pages/CommitteesPage'
import HierarchyPage from './pages/HierarchyPage'
import AdminDashboard from './pages/AdminDashboard'
import SuperAdminPage from './pages/SuperAdminPage'
import CircularProgress from '@mui/material/CircularProgress'
import Box from '@mui/material/Box'

// Protected Route Component
function ProtectedRoute({ children, requireAdmin = false, requireSuperAdmin = false }) {
    const { isAuthenticated, loading, isAdmin, user } = useAuth()

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
                <CircularProgress />
            </Box>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    if (requireSuperAdmin && !user?.is_super_admin) {
        return <Navigate to="/dashboard" replace />
    }

    if (requireAdmin && !isAdmin) {
        return <Navigate to="/dashboard" replace />
    }

    return children
}

function AppRoutes() {
    return (
        <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected routes */}
            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <Layout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="committees" element={<CommitteesPage />} />
                <Route path="hierarchy" element={<HierarchyPage />} />

                {/* Admin routes */}
                <Route
                    path="admin"
                    element={
                        <ProtectedRoute requireAdmin>
                            <AdminDashboard />
                        </ProtectedRoute>
                    }
                />

                {/* Super Admin routes */}
                <Route
                    path="super-admin"
                    element={
                        <ProtectedRoute requireSuperAdmin>
                            <SuperAdminPage />
                        </ProtectedRoute>
                    }
                />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

function App() {
    return (
        <TenantProvider>
            <TenantThemeProvider>
                <AuthProvider>
                    <AppRoutes />
                </AuthProvider>
            </TenantThemeProvider>
        </TenantProvider>
    )
}

export default App
