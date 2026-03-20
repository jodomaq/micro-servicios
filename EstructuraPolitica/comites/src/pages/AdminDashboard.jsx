/**
 * AdminDashboard - Panel de administración
 * Gestión de coordinadores, asignación de roles, tipos de comité y configuración visual
 */
import { useState, useEffect } from 'react'
import {
    Box,
    Paper,
    Typography,
    Tabs,
    Tab,
    Button,
    IconButton,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Chip,
    Alert,
    Snackbar,
    CircularProgress,
} from '@mui/material'
import {
    PersonAdd,
    Group,
    AccountTree,
    Delete,
    Edit,
    Assignment,
    Category as CategoryIcon,
    Add as AddIcon,
} from '@mui/icons-material'
import api from '../services/api'

function TabPanel({ children, value, index }) {
    return (
        <div role="tabpanel" hidden={value !== index}>
            {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
        </div>
    )
}

const ROLES = [
    { value: 1, label: 'Coordinador Estatal' },
    { value: 2, label: 'Delegado Regional' },
    { value: 3, label: 'Coordinador Distrital' },
    { value: 4, label: 'Coordinador Municipal' },
    { value: 5, label: 'Coordinador Seccional' },
    { value: 6, label: 'Presidente de Comité' },
    { value: 7, label: 'Capturista' },
]

const ROLE_LABELS = Object.fromEntries(ROLES.map(r => [r.value, r.label]))

const USER_ROLES_FOR_CREATION = [
    { value: 'COORDINATOR', label: 'Coordinador' },
    { value: 'ADMIN', label: 'Administrador' },
    { value: 'VIEWER', label: 'Visualizador' },
]

export default function AdminDashboard() {
    const [tabValue, setTabValue] = useState(0)
    const [users, setUsers] = useState([])
    const [assignments, setAssignments] = useState([])
    const [adminUnits, setAdminUnits] = useState([])
    const [committeeTypes, setCommitteeTypes] = useState([])
    const [loading, setLoading] = useState(false)
    const [openUserDialog, setOpenUserDialog] = useState(false)
    const [openAssignDialog, setOpenAssignDialog] = useState(false)
    const [openTypeDialog, setOpenTypeDialog] = useState(false)
    const [editingUser, setEditingUser] = useState(null)
    const [editingType, setEditingType] = useState(null)
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' })
    
    const [userForm, setUserForm] = useState({ email: '', full_name: '', role: 'COORDINATOR', password: '' })
    const [assignForm, setAssignForm] = useState({ user_id: '', unit_id: '', role: 7 })
    const [typeForm, setTypeForm] = useState({ name: '', description: '', max_members: 10 })

    useEffect(() => {
        if (tabValue === 0) loadUsers()
        if (tabValue === 1) { loadAssignments(); loadAdminUnits(); if (users.length === 0) loadUsers() }
        if (tabValue === 2) loadCommitteeTypes()
    }, [tabValue])

    const loadUsers = async () => {
        setLoading(true)
        try { setUsers((await api.get('/users')).data) }
        catch { showSnackbar('Error al cargar usuarios', 'error') }
        finally { setLoading(false) }
    }
    const loadAssignments = async () => {
        setLoading(true)
        try { setAssignments((await api.get('/users/assignments')).data) }
        catch { showSnackbar('Error al cargar asignaciones', 'error') }
        finally { setLoading(false) }
    }
    const loadAdminUnits = async () => {
        try { setAdminUnits((await api.get('/administrative-units')).data) }
        catch (e) { console.error(e) }
    }
    const loadCommitteeTypes = async () => {
        setLoading(true)
        try { setCommitteeTypes((await api.get('/committee-types')).data) }
        catch { showSnackbar('Error al cargar tipos de comité', 'error') }
        finally { setLoading(false) }
    }

    // User CRUD
    const handleOpenUserDialog = (user = null) => {
        if (user) {
            setEditingUser(user)
            setUserForm({ email: user.email, full_name: user.full_name || user.name, role: user.role || 'COORDINATOR', password: '' })
        } else {
            setEditingUser(null)
            setUserForm({ email: '', full_name: '', role: 'COORDINATOR', password: '' })
        }
        setOpenUserDialog(true)
    }
    const handleSaveUser = async () => {
        try {
            if (editingUser) {
                await api.put(`/users/${editingUser.id}`, userForm)
                showSnackbar('Usuario actualizado')
            } else {
                await api.post('/users', userForm)
                showSnackbar('Usuario creado')
            }
            setOpenUserDialog(false); setEditingUser(null); loadUsers()
        } catch (e) { showSnackbar(e.response?.data?.detail || 'Error', 'error') }
    }
    const handleDeleteUser = async (id) => {
        if (!window.confirm('¿Eliminar usuario?')) return
        try { await api.delete(`/users/${id}`); showSnackbar('Eliminado'); loadUsers() }
        catch { showSnackbar('Error', 'error') }
    }

    // Assignment CRUD
    const handleOpenAssignDialog = () => {
        setAssignForm({ user_id: '', unit_id: '', role: 7 })
        setOpenAssignDialog(true)
    }
    const handleSaveAssignment = async () => {
        try { await api.post('/users/assignments', assignForm); showSnackbar('Asignación creada'); setOpenAssignDialog(false); loadAssignments() }
        catch (e) { showSnackbar(e.response?.data?.detail || 'Error', 'error') }
    }
    const handleDeleteAssignment = async (id) => {
        if (!window.confirm('¿Eliminar asignación?')) return
        try { await api.delete(`/users/assignments/${id}`); showSnackbar('Eliminada'); loadAssignments() }
        catch { showSnackbar('Error', 'error') }
    }

    // Committee Type CRUD
    const handleOpenTypeDialog = (type = null) => {
        if (type) {
            setEditingType(type)
            setTypeForm({ name: type.name, description: type.description || '', max_members: type.max_members || 10 })
        } else {
            setEditingType(null)
            setTypeForm({ name: '', description: '', max_members: 10 })
        }
        setOpenTypeDialog(true)
    }
    const handleSaveType = async () => {
        try {
            if (editingType) {
                await api.put(`/committee-types/${editingType.id}`, typeForm)
                showSnackbar('Tipo actualizado')
            } else {
                await api.post('/committee-types', typeForm)
                showSnackbar('Tipo creado')
            }
            setOpenTypeDialog(false); setEditingType(null); loadCommitteeTypes()
        } catch (e) { showSnackbar(e.response?.data?.detail || 'Error', 'error') }
    }
    const handleDeleteType = async (id) => {
        if (!window.confirm('¿Eliminar tipo de comité?')) return
        try { await api.delete(`/committee-types/${id}`); showSnackbar('Eliminado'); loadCommitteeTypes() }
        catch { showSnackbar('Error', 'error') }
    }

    const showSnackbar = (message, severity = 'success') => setSnackbar({ open: true, message, severity })
    const getRoleLabel = (role) => ({ SUPER_ADMIN: 'Super Admin', ADMIN: 'Administrador', COORDINATOR: 'Coordinador', VIEWER: 'Visualizador' }[role] || role)
    const getRoleColor = (role) => ({ SUPER_ADMIN: 'error', ADMIN: 'warning', COORDINATOR: 'primary', VIEWER: 'default' }[role] || 'default')

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={1}>
                <Typography variant="h4" fontWeight="bold">Panel de Administración</Typography>
                {tabValue === 0 && <Button variant="contained" startIcon={<PersonAdd />} onClick={() => handleOpenUserDialog()}>Nuevo Usuario</Button>}
                {tabValue === 1 && <Button variant="contained" startIcon={<Assignment />} onClick={handleOpenAssignDialog}>Nueva Asignación</Button>}
                {tabValue === 2 && <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenTypeDialog()}>Nuevo Tipo</Button>}
            </Box>

            <Paper>
                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} variant="scrollable" scrollButtons="auto">
                    <Tab label="Usuarios" icon={<Group />} iconPosition="start" />
                    <Tab label="Asignaciones" icon={<AccountTree />} iconPosition="start" />
                    <Tab label="Tipos de Comité" icon={<CategoryIcon />} iconPosition="start" />
                </Tabs>

                {/* Tab 0: Users */}
                <TabPanel value={tabValue} index={0}>
                    {loading ? <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box> : (
                        <TableContainer>
                            <Table>
                                <TableHead><TableRow>
                                    <TableCell>Nombre</TableCell><TableCell>Email</TableCell><TableCell>Rol</TableCell><TableCell>Estado</TableCell><TableCell align="right">Acciones</TableCell>
                                </TableRow></TableHead>
                                <TableBody>
                                    {users.map((user) => (
                                        <TableRow key={user.id}>
                                            <TableCell>{user.full_name || user.name}</TableCell>
                                            <TableCell>{user.email}</TableCell>
                                            <TableCell><Chip label={getRoleLabel(user.role)} color={getRoleColor(user.role)} size="small" /></TableCell>
                                            <TableCell><Chip label={user.is_active ? 'Activo' : 'Inactivo'} color={user.is_active ? 'success' : 'default'} size="small" /></TableCell>
                                            <TableCell align="right">
                                                <IconButton size="small" onClick={() => handleOpenUserDialog(user)}><Edit /></IconButton>
                                                <IconButton size="small" color="error" onClick={() => handleDeleteUser(user.id)}><Delete /></IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </TabPanel>

                {/* Tab 1: Assignments */}
                <TabPanel value={tabValue} index={1}>
                    {loading ? <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box> : (
                        <TableContainer>
                            <Table>
                                <TableHead><TableRow>
                                    <TableCell>Usuario</TableCell><TableCell>Unidad Administrativa</TableCell><TableCell>Rol</TableCell><TableCell align="right">Acciones</TableCell>
                                </TableRow></TableHead>
                                <TableBody>
                                    {assignments.map((a) => (
                                        <TableRow key={a.id}>
                                            <TableCell>{a.user?.full_name || a.user?.name || 'N/A'}</TableCell>
                                            <TableCell>{a.administrative_unit?.name || 'N/A'}</TableCell>
                                            <TableCell><Chip label={ROLE_LABELS[a.role] || `Rol ${a.role}`} size="small" color="primary" variant="outlined" /></TableCell>
                                            <TableCell align="right">
                                                <IconButton size="small" color="error" onClick={() => handleDeleteAssignment(a.id)}><Delete /></IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </TabPanel>

                {/* Tab 2: Committee Types */}
                <TabPanel value={tabValue} index={2}>
                    {loading ? <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box> : (
                        <TableContainer>
                            <Table>
                                <TableHead><TableRow>
                                    <TableCell>Nombre</TableCell><TableCell>Descripción</TableCell><TableCell>Max Miembros</TableCell><TableCell align="right">Acciones</TableCell>
                                </TableRow></TableHead>
                                <TableBody>
                                    {committeeTypes.map((t) => (
                                        <TableRow key={t.id}>
                                            <TableCell>{t.name}</TableCell>
                                            <TableCell>{t.description || '-'}</TableCell>
                                            <TableCell>{t.max_members || 10}</TableCell>
                                            <TableCell align="right">
                                                <IconButton size="small" onClick={() => handleOpenTypeDialog(t)}><Edit /></IconButton>
                                                <IconButton size="small" color="error" onClick={() => handleDeleteType(t.id)}><Delete /></IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </TabPanel>
            </Paper>

            {/* Dialog: User */}
            <Dialog open={openUserDialog} onClose={() => { setOpenUserDialog(false); setEditingUser(null) }} maxWidth="sm" fullWidth>
                <DialogTitle>{editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                        <TextField label="Nombre Completo" fullWidth value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} required />
                        <TextField label="Email" type="email" fullWidth value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} required />
                        <FormControl fullWidth><InputLabel>Rol</InputLabel>
                            <Select value={userForm.role} label="Rol" onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
                                {USER_ROLES_FOR_CREATION.map(r => <MenuItem key={r.value} value={r.value}>{r.label}</MenuItem>)}
                            </Select>
                        </FormControl>
                        {!editingUser && <TextField label="Contraseña" type="password" fullWidth value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} required helperText="Mínimo 8 caracteres" />}
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => { setOpenUserDialog(false); setEditingUser(null) }}>Cancelar</Button>
                    <Button onClick={handleSaveUser} variant="contained" disabled={!userForm.email || !userForm.full_name || (!editingUser && !userForm.password)}>
                        {editingUser ? 'Actualizar' : 'Crear'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Dialog: Assignment */}
            <Dialog open={openAssignDialog} onClose={() => setOpenAssignDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Nueva Asignación</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                        <FormControl fullWidth><InputLabel>Usuario</InputLabel>
                            <Select value={assignForm.user_id} label="Usuario" onChange={(e) => setAssignForm({ ...assignForm, user_id: e.target.value })}>
                                {users.map((u) => <MenuItem key={u.id} value={u.id}>{u.full_name || u.name} ({u.email})</MenuItem>)}
                            </Select>
                        </FormControl>
                        <FormControl fullWidth><InputLabel>Unidad Administrativa</InputLabel>
                            <Select value={assignForm.unit_id} label="Unidad Administrativa" onChange={(e) => setAssignForm({ ...assignForm, unit_id: e.target.value })}>
                                {adminUnits.map((u) => <MenuItem key={u.id} value={u.id}>{u.name} ({u.unit_type})</MenuItem>)}
                            </Select>
                        </FormControl>
                        <FormControl fullWidth><InputLabel>Rol Jerárquico</InputLabel>
                            <Select value={assignForm.role} label="Rol Jerárquico" onChange={(e) => setAssignForm({ ...assignForm, role: e.target.value })}>
                                {ROLES.map(r => <MenuItem key={r.value} value={r.value}>{r.label}</MenuItem>)}
                            </Select>
                        </FormControl>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenAssignDialog(false)}>Cancelar</Button>
                    <Button onClick={handleSaveAssignment} variant="contained" disabled={!assignForm.user_id || !assignForm.unit_id}>Crear</Button>
                </DialogActions>
            </Dialog>

            {/* Dialog: Committee Type */}
            <Dialog open={openTypeDialog} onClose={() => { setOpenTypeDialog(false); setEditingType(null) }} maxWidth="sm" fullWidth>
                <DialogTitle>{editingType ? 'Editar Tipo de Comité' : 'Nuevo Tipo de Comité'}</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                        <TextField label="Nombre" fullWidth value={typeForm.name} onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })} required />
                        <TextField label="Descripción" fullWidth multiline rows={2} value={typeForm.description} onChange={(e) => setTypeForm({ ...typeForm, description: e.target.value })} />
                        <TextField label="Máximo de Miembros" type="number" fullWidth value={typeForm.max_members}
                            onChange={(e) => setTypeForm({ ...typeForm, max_members: parseInt(e.target.value) || 10 })}
                            inputProps={{ min: 1, max: 100 }} />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => { setOpenTypeDialog(false); setEditingType(null) }}>Cancelar</Button>
                    <Button onClick={handleSaveType} variant="contained" disabled={!typeForm.name}>
                        {editingType ? 'Actualizar' : 'Crear'}
                    </Button>
                </DialogActions>
            </Dialog>

            <Snackbar open={snackbar.open} autoHideDuration={5000} onClose={() => setSnackbar({ ...snackbar, open: false })} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
                <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} variant="filled">{snackbar.message}</Alert>
            </Snackbar>
        </Box>
    )
}
