/**
 * SuperAdminPage - Panel de Super Administración SaaS
 * Gestión global de tenants, estadísticas, planes y logs de auditoría
 */
import { useState, useEffect } from 'react'
import {
    Box, Paper, Typography, Tabs, Tab, Button, IconButton,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Dialog, DialogTitle, DialogContent, DialogActions, TextField,
    Select, MenuItem, FormControl, InputLabel, Chip, Alert, Snackbar,
    CircularProgress, Card, CardContent, Grid, Switch, FormControlLabel,
    TablePagination,
} from '@mui/material'
import {
    Business, BarChart, Receipt, Edit, Block, CheckCircle,
    Refresh as RefreshIcon,
} from '@mui/icons-material'
import api from '../services/api'

function TabPanel({ children, value, index }) {
    return <div role="tabpanel" hidden={value !== index}>{value === index && <Box sx={{ p: 3 }}>{children}</Box>}</div>
}

const STATUS_COLORS = {
    trial: 'warning', active: 'success', past_due: 'error',
    cancelled: 'default', suspended: 'error',
}

export default function SuperAdminPage() {
    const [tabValue, setTabValue] = useState(0)
    const [loading, setLoading] = useState(false)
    const [tenants, setTenants] = useState([])
    const [stats, setStats] = useState(null)
    const [auditLogs, setAuditLogs] = useState([])
    const [plans, setPlans] = useState([])
    const [editDialog, setEditDialog] = useState(false)
    const [editingTenant, setEditingTenant] = useState(null)
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' })
    const [logPage, setLogPage] = useState(0)

    useEffect(() => {
        if (tabValue === 0) { loadTenants(); loadStats() }
        if (tabValue === 1) loadAuditLogs()
        if (tabValue === 2) loadPlans()
    }, [tabValue])

    const loadTenants = async () => {
        setLoading(true)
        try { setTenants((await api.get('/admin/tenants')).data) }
        catch { showSnackbar('Error cargando tenants', 'error') }
        finally { setLoading(false) }
    }
    const loadStats = async () => {
        try { setStats((await api.get('/admin/stats')).data) } catch { }
    }
    const loadAuditLogs = async () => {
        setLoading(true)
        try { setAuditLogs((await api.get('/admin/audit-logs?limit=100')).data) }
        catch { showSnackbar('Error cargando logs', 'error') }
        finally { setLoading(false) }
    }
    const loadPlans = async () => {
        setLoading(true)
        try { setPlans((await api.get('/admin/plans')).data) }
        catch { showSnackbar('Error cargando planes', 'error') }
        finally { setLoading(false) }
    }

    const handleToggleTenant = async (tenant) => {
        const action = tenant.subscription_status === 'suspended' ? 'active' : 'suspended'
        try {
            await api.put(`/admin/tenants/${tenant.id}`, { subscription_status: action })
            showSnackbar(`Tenant ${action === 'suspended' ? 'suspendido' : 'reactivado'}`)
            loadTenants()
        } catch { showSnackbar('Error', 'error') }
    }

    const handleEditTenant = (tenant) => {
        setEditingTenant({ ...tenant })
        setEditDialog(true)
    }

    const handleSaveTenant = async () => {
        try {
            await api.put(`/admin/tenants/${editingTenant.id}`, {
                name: editingTenant.name,
                subscription_status: editingTenant.subscription_status,
                plan_id: editingTenant.plan_id,
                max_users: editingTenant.max_users,
                max_committees: editingTenant.max_committees,
            })
            showSnackbar('Tenant actualizado')
            setEditDialog(false); loadTenants()
        } catch { showSnackbar('Error al actualizar', 'error') }
    }

    const showSnackbar = (message, severity = 'success') => setSnackbar({ open: true, message, severity })

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" fontWeight="bold">Super Administración</Typography>
                <Button startIcon={<RefreshIcon />} onClick={() => { loadTenants(); loadStats() }}>Actualizar</Button>
            </Box>

            {/* Stats Cards */}
            {stats && (
                <Grid container spacing={2} mb={3}>
                    {[
                        { label: 'Tenants Totales', value: stats.total_tenants, color: '#1976d2' },
                        { label: 'Tenants Activos', value: stats.active_tenants, color: '#2e7d32' },
                        { label: 'Usuarios Totales', value: stats.total_users, color: '#ed6c02' },
                        { label: 'Comités Totales', value: stats.total_committees, color: '#9c27b0' },
                    ].map((item, i) => (
                        <Grid item xs={6} md={3} key={i}>
                            <Card>
                                <CardContent sx={{ textAlign: 'center' }}>
                                    <Typography variant="h4" fontWeight="bold" color={item.color}>{item.value ?? 0}</Typography>
                                    <Typography variant="body2" color="text.secondary">{item.label}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            )}

            <Paper>
                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} variant="scrollable" scrollButtons="auto">
                    <Tab label="Tenants" icon={<Business />} iconPosition="start" />
                    <Tab label="Auditoría" icon={<Receipt />} iconPosition="start" />
                    <Tab label="Planes" icon={<BarChart />} iconPosition="start" />
                </Tabs>

                {/* Tenants */}
                <TabPanel value={tabValue} index={0}>
                    {loading ? <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box> : (
                        <TableContainer>
                            <Table size="small">
                                <TableHead><TableRow>
                                    <TableCell>ID</TableCell><TableCell>Nombre</TableCell><TableCell>Subdominio</TableCell>
                                    <TableCell>Estado</TableCell><TableCell>Plan</TableCell><TableCell>Usuarios</TableCell>
                                    <TableCell align="right">Acciones</TableCell>
                                </TableRow></TableHead>
                                <TableBody>
                                    {tenants.map(t => (
                                        <TableRow key={t.id}>
                                            <TableCell>{t.id}</TableCell>
                                            <TableCell>{t.name}</TableCell>
                                            <TableCell>{t.subdomain}</TableCell>
                                            <TableCell><Chip label={t.subscription_status} size="small" color={STATUS_COLORS[t.subscription_status] || 'default'} /></TableCell>
                                            <TableCell>{t.subscription_plan?.name || '-'}</TableCell>
                                            <TableCell>{t.max_users || '∞'}</TableCell>
                                            <TableCell align="right">
                                                <IconButton size="small" onClick={() => handleEditTenant(t)}><Edit /></IconButton>
                                                <IconButton size="small" color={t.subscription_status === 'suspended' ? 'success' : 'error'}
                                                    onClick={() => handleToggleTenant(t)}>
                                                    {t.subscription_status === 'suspended' ? <CheckCircle /> : <Block />}
                                                </IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </TabPanel>

                {/* Audit Logs */}
                <TabPanel value={tabValue} index={1}>
                    {loading ? <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box> : (
                        <>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead><TableRow>
                                        <TableCell>Fecha</TableCell><TableCell>Tenant</TableCell><TableCell>Usuario</TableCell>
                                        <TableCell>Acción</TableCell><TableCell>Entidad</TableCell><TableCell>Detalles</TableCell>
                                    </TableRow></TableHead>
                                    <TableBody>
                                        {auditLogs.slice(logPage * 20, logPage * 20 + 20).map(log => (
                                            <TableRow key={log.id}>
                                                <TableCell sx={{ whiteSpace: 'nowrap' }}>{new Date(log.created_at).toLocaleString()}</TableCell>
                                                <TableCell>{log.tenant_id}</TableCell>
                                                <TableCell>{log.user_id}</TableCell>
                                                <TableCell><Chip label={log.action} size="small" /></TableCell>
                                                <TableCell>{log.entity_type} #{log.entity_id}</TableCell>
                                                <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.details}</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                            <TablePagination component="div" count={auditLogs.length} page={logPage}
                                onPageChange={(_, p) => setLogPage(p)} rowsPerPage={20} rowsPerPageOptions={[20]} />
                        </>
                    )}
                </TabPanel>

                {/* Plans */}
                <TabPanel value={tabValue} index={2}>
                    {loading ? <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box> : (
                        <Grid container spacing={2}>
                            {plans.map(plan => (
                                <Grid item xs={12} sm={6} md={3} key={plan.id}>
                                    <Card variant="outlined">
                                        <CardContent>
                                            <Typography variant="h6" gutterBottom>{plan.name}</Typography>
                                            <Typography variant="h5" color="primary" gutterBottom>
                                                ${plan.price_monthly || 0}/mes
                                            </Typography>
                                            <Typography variant="body2">Max usuarios: {plan.max_users || '∞'}</Typography>
                                            <Typography variant="body2">Max comités: {plan.max_committees || '∞'}</Typography>
                                            <Typography variant="body2">Max eventos: {plan.max_events || '∞'}</Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>
                    )}
                </TabPanel>
            </Paper>

            {/* Edit Tenant Dialog */}
            <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Editar Tenant</DialogTitle>
                <DialogContent>
                    {editingTenant && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                            <TextField label="Nombre" fullWidth value={editingTenant.name || ''}
                                onChange={(e) => setEditingTenant({ ...editingTenant, name: e.target.value })} />
                            <FormControl fullWidth><InputLabel>Estado</InputLabel>
                                <Select value={editingTenant.subscription_status || 'trial'} label="Estado"
                                    onChange={(e) => setEditingTenant({ ...editingTenant, subscription_status: e.target.value })}>
                                    <MenuItem value="trial">Trial</MenuItem>
                                    <MenuItem value="active">Activo</MenuItem>
                                    <MenuItem value="suspended">Suspendido</MenuItem>
                                    <MenuItem value="cancelled">Cancelado</MenuItem>
                                </Select>
                            </FormControl>
                            <TextField label="Max Usuarios" type="number" fullWidth value={editingTenant.max_users || ''}
                                onChange={(e) => setEditingTenant({ ...editingTenant, max_users: parseInt(e.target.value) || null })} />
                            <TextField label="Max Comités" type="number" fullWidth value={editingTenant.max_committees || ''}
                                onChange={(e) => setEditingTenant({ ...editingTenant, max_committees: parseInt(e.target.value) || null })} />
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditDialog(false)}>Cancelar</Button>
                    <Button onClick={handleSaveTenant} variant="contained">Guardar</Button>
                </DialogActions>
            </Dialog>

            <Snackbar open={snackbar.open} autoHideDuration={5000} onClose={() => setSnackbar({ ...snackbar, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
                <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} variant="filled">{snackbar.message}</Alert>
            </Snackbar>
        </Box>
    )
}
