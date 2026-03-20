/**
 * Componente de Layout principal con AppBar y navegación
 */
import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
    AppBar,
    Box,
    Toolbar,
    IconButton,
    Typography,
    Menu,
    Container,
    Avatar,
    Button,
    Tooltip,
    MenuItem,
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Divider,
} from '@mui/material'
import {
    Menu as MenuIcon,
    Dashboard as DashboardIcon,
    People as PeopleIcon,
    Event as EventIcon,
    Poll as PollIcon,
    AccountTree as HierarchyIcon,
    AccountCircle,
    Logout,
    Settings,
    AdminPanelSettings,
    SupervisorAccount as SuperAdminIcon,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { useTenant } from '../contexts/TenantContext'

const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Comités', icon: <PeopleIcon />, path: '/committees' },
    { text: 'Jerarquía', icon: <HierarchyIcon />, path: '/hierarchy' },
]

const adminMenuItems = [
    { text: 'Admin Panel', icon: <AdminPanelSettings />, path: '/admin' },
]

const superAdminMenuItems = [
    { text: 'Super Admin', icon: <SuperAdminIcon />, path: '/super-admin' },
]

export default function Layout() {
    const navigate = useNavigate()
    const location = useLocation()
    const { user, logout, isAdmin } = useAuth()
    const { tenant } = useTenant()
    const isSuperAdmin = user?.is_super_admin

    const [mobileOpen, setMobileOpen] = useState(false)
    const [anchorElUser, setAnchorElUser] = useState(null)

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen)
    }

    const handleOpenUserMenu = (event) => {
        setAnchorElUser(event.currentTarget)
    }

    const handleCloseUserMenu = () => {
        setAnchorElUser(null)
    }

    const handleNavigate = (path) => {
        navigate(path)
        setMobileOpen(false)
    }

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    const drawer = (
        <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
            <Typography variant="h6" sx={{ my: 2, color: 'primary.main' }}>
                {tenant?.name || 'Sistema'}
            </Typography>
            <Divider />
            <List>
                {menuItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton
                            selected={location.pathname === item.path}
                            onClick={() => handleNavigate(item.path)}
                        >
                            <ListItemIcon>{item.icon}</ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItemButton>
                    </ListItem>
                ))}

                {isAdmin && (
                    <>
                        <Divider sx={{ my: 1 }} />
                        {adminMenuItems.map((item) => (
                            <ListItem key={item.text} disablePadding>
                                <ListItemButton
                                    selected={location.pathname === item.path}
                                    onClick={() => handleNavigate(item.path)}
                                >
                                    <ListItemIcon>{item.icon}</ListItemIcon>
                                    <ListItemText primary={item.text} />
                                </ListItemButton>
                            </ListItem>
                        ))}
                    </>
                )}

                {isSuperAdmin && (
                    <>
                        <Divider sx={{ my: 1 }} />
                        {superAdminMenuItems.map((item) => (
                            <ListItem key={item.text} disablePadding>
                                <ListItemButton
                                    selected={location.pathname === item.path}
                                    onClick={() => handleNavigate(item.path)}
                                >
                                    <ListItemIcon>{item.icon}</ListItemIcon>
                                    <ListItemText primary={item.text} />
                                </ListItemButton>
                            </ListItem>
                        ))}
                    </>
                )}
            </List>
        </Box>
    )

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <AppBar position="sticky">
                <Container maxWidth="xl">
                    <Toolbar disableGutters>
                        {/* Hamburger menu - mobile */}
                        <IconButton
                            color="inherit"
                            aria-label="open drawer"
                            edge="start"
                            onClick={handleDrawerToggle}
                            sx={{ mr: 2, display: { sm: 'block', md: 'none' } }}
                        >
                            <MenuIcon />
                        </IconButton>

                        {/* Logo */}
                        {tenant?.logo_url ? (
                            <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                                <img
                                    src={tenant.logo_url}
                                    alt={tenant.name}
                                    style={{ height: 40, marginRight: 12 }}
                                />
                            </Box>
                        ) : (
                            <Typography
                                variant="h6"
                                noWrap
                                component="div"
                                sx={{ mr: 2, fontWeight: 700 }}
                            >
                                {tenant?.name || 'Sistema'}
                            </Typography>
                        )}

                        {/* Desktop menu */}
                        <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
                            {menuItems.map((item) => (
                                <Button
                                    key={item.text}
                                    onClick={() => handleNavigate(item.path)}
                                    sx={{
                                        my: 2,
                                        color: 'white',
                                        display: 'block',
                                        fontWeight: location.pathname === item.path ? 700 : 400,
                                    }}
                                    startIcon={item.icon}
                                >
                                    {item.text}
                                </Button>
                            ))}
                            {isAdmin && adminMenuItems.map((item) => (
                                <Button
                                    key={item.text}
                                    onClick={() => handleNavigate(item.path)}
                                    sx={{
                                        my: 2,
                                        color: 'white',
                                        display: 'block',
                                        fontWeight: location.pathname === item.path ? 700 : 400,
                                    }}
                                    startIcon={item.icon}
                                >
                                    {item.text}
                                </Button>
                            ))}
                            {isSuperAdmin && superAdminMenuItems.map((item) => (
                                <Button
                                    key={item.text}
                                    onClick={() => handleNavigate(item.path)}
                                    sx={{
                                        my: 2,
                                        color: 'white',
                                        display: 'block',
                                        fontWeight: location.pathname === item.path ? 700 : 400,
                                    }}
                                    startIcon={item.icon}
                                >
                                    {item.text}
                                </Button>
                            ))}
                        </Box>

                        {/* User menu */}
                        <Box sx={{ flexGrow: 0 }}>
                            <Tooltip title="Mi cuenta">
                                <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                                    <Avatar
                                        alt={user?.name}
                                        src={user?.picture_url}
                                        sx={{ bgcolor: 'secondary.main' }}
                                    >
                                        {user?.name?.charAt(0)}
                                    </Avatar>
                                </IconButton>
                            </Tooltip>
                            <Menu
                                sx={{ mt: '45px' }}
                                id="menu-appbar"
                                anchorEl={anchorElUser}
                                anchorOrigin={{
                                    vertical: 'top',
                                    horizontal: 'right',
                                }}
                                keepMounted
                                transformOrigin={{
                                    vertical: 'top',
                                    horizontal: 'right',
                                }}
                                open={Boolean(anchorElUser)}
                                onClose={handleCloseUserMenu}
                            >
                                <MenuItem disabled>
                                    <Typography textAlign="center" variant="body2">
                                        {user?.name}
                                        <br />
                                        <Typography variant="caption" color="text.secondary">
                                            {user?.email}
                                        </Typography>
                                    </Typography>
                                </MenuItem>
                                <Divider />
                                <MenuItem onClick={() => { handleCloseUserMenu(); navigate('/profile'); }}>
                                    <ListItemIcon>
                                        <AccountCircle fontSize="small" />
                                    </ListItemIcon>
                                    Mi Perfil
                                </MenuItem>
                                {isAdmin && (
                                    <MenuItem onClick={() => { handleCloseUserMenu(); navigate('/settings'); }}>
                                        <ListItemIcon>
                                            <Settings fontSize="small" />
                                        </ListItemIcon>
                                        Configuración
                                    </MenuItem>
                                )}
                                <Divider />
                                <MenuItem onClick={handleLogout}>
                                    <ListItemIcon>
                                        <Logout fontSize="small" />
                                    </ListItemIcon>
                                    Cerrar Sesión
                                </MenuItem>
                            </Menu>
                        </Box>
                    </Toolbar>
                </Container>
            </AppBar>

            {/* Mobile drawer */}
            <Drawer
                variant="temporary"
                open={mobileOpen}
                onClose={handleDrawerToggle}
                ModalProps={{
                    keepMounted: true, // Better open performance on mobile
                }}
                sx={{
                    display: { xs: 'block', md: 'none' },
                    '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
                }}
            >
                {drawer}
            </Drawer>

            {/* Main content */}
            <Box component="main" sx={{ flexGrow: 1, p: 3, backgroundColor: '#f5f5f5' }}>
                <Container maxWidth="xl">
                    <Outlet />
                </Container>
            </Box>
        </Box>
    )
}
