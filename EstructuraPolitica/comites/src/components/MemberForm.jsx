/**
 * Formulario para agregar/editar miembros del comité
 * Muestra miembros existentes con edición/eliminación y slots para nuevos
 */
import { useState, useEffect } from 'react'
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Grid,
    Box,
    Alert,
    CircularProgress,
    IconButton,
    Typography,
    Divider,
    Chip,
    Tabs,
    Tab,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
} from '@mui/material'
import { 
    Save as SaveIcon, 
    Cancel as CancelIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
    PersonAdd as PersonAddIcon,
} from '@mui/icons-material'
import api from '../services/api'

const MAX_MEMBERS = 10

const EMPTY_MEMBER = {
    full_name: '',
    ine_key: '',
    phone: '',
    email: '',
    section_number: '',
    referred_by: '',
}

export default function MemberForm({ open, onClose, onSave, committeeId }) {
    const [loading, setLoading] = useState(false)
    const [loadingExisting, setLoadingExisting] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(false)
    const [tabValue, setTabValue] = useState(0)
    
    // Miembros existentes
    const [existingMembers, setExistingMembers] = useState([])
    const [editingMember, setEditingMember] = useState(null) // member being edited
    
    // Nuevos miembros para agregar
    const [newMembers, setNewMembers] = useState([{ ...EMPTY_MEMBER }])

    useEffect(() => {
        if (open && committeeId) {
            loadExistingMembers()
            setNewMembers([{ ...EMPTY_MEMBER }])
            setError(null)
            setSuccess(false)
            setEditingMember(null)
        }
    }, [open, committeeId])

    const loadExistingMembers = async () => {
        setLoadingExisting(true)
        try {
            const response = await api.get(`/committees/${committeeId}/members`)
            setExistingMembers(response.data)
        } catch (err) {
            console.error('Error loading members:', err)
        } finally {
            setLoadingExisting(false)
        }
    }

    const availableSlots = MAX_MEMBERS - existingMembers.length

    const handleNewMemberChange = (index, field, value) => {
        setNewMembers(prev => {
            const updated = [...prev]
            updated[index] = { ...updated[index], [field]: value }
            return updated
        })
    }

    const addNewMemberSlot = () => {
        if (newMembers.length < availableSlots) {
            setNewMembers(prev => [...prev, { ...EMPTY_MEMBER }])
        }
    }

    const removeNewMemberSlot = (index) => {
        setNewMembers(prev => prev.filter((_, i) => i !== index))
    }

    const handleDeleteExisting = async (memberId) => {
        if (!window.confirm('¿Eliminar este miembro?')) return
        try {
            await api.delete(`/committees/${committeeId}/members/${memberId}`)
            setExistingMembers(prev => prev.filter(m => m.id !== memberId))
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar miembro')
        }
    }

    const handleEditExisting = (member) => {
        setEditingMember({ ...member })
    }

    const handleSaveEditedMember = async () => {
        if (!editingMember) return
        try {
            setLoading(true)
            await api.put(`/committees/${committeeId}/members/${editingMember.id}`, {
                full_name: editingMember.full_name,
                ine_key: editingMember.ine_key,
                phone: editingMember.phone,
                email: editingMember.email,
                section_number: editingMember.section_number,
                referred_by: editingMember.referred_by,
            })
            await loadExistingMembers()
            setEditingMember(null)
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al actualizar miembro')
        } finally {
            setLoading(false)
        }
    }

    const handleSubmitNew = async (e) => {
        e.preventDefault()
        const validMembers = newMembers.filter(m => m.full_name && m.ine_key)
        if (validMembers.length === 0) {
            setError('Agregue al menos un miembro con nombre y clave de INE')
            return
        }
        setLoading(true)
        setError(null)
        try {
            await Promise.all(
                validMembers.map(m => api.post(`/committees/${committeeId}/members`, m))
            )
            setSuccess(true)
            setTimeout(() => { onSave(); onClose() }, 1000)
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Error al guardar'
            setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
            <DialogTitle>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                    <span>Miembros del Comité</span>
                    <Chip
                        label={`${existingMembers.length} / ${MAX_MEMBERS} miembros`}
                        color={existingMembers.length >= MAX_MEMBERS ? 'error' : 'primary'}
                        variant="outlined"
                    />
                </Box>
            </DialogTitle>

            <DialogContent>
                {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
                {success && <Alert severity="success" sx={{ mb: 2 }}>¡Miembros guardados exitosamente!</Alert>}

                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
                    <Tab label={`Existentes (${existingMembers.length})`} />
                    <Tab label="Agregar Nuevos" disabled={availableSlots <= 0} />
                </Tabs>

                {/* Tab: Existing Members */}
                {tabValue === 0 && (
                    <Box>
                        {loadingExisting ? (
                            <Box display="flex" justifyContent="center" p={3}><CircularProgress /></Box>
                        ) : existingMembers.length === 0 ? (
                            <Typography color="text.secondary" textAlign="center" py={3}>
                                No hay miembros registrados aún
                            </Typography>
                        ) : (
                            <List>
                                {existingMembers.map((member) => (
                                    <ListItem key={member.id} divider>
                                        {editingMember?.id === member.id ? (
                                            <Grid container spacing={1} alignItems="center">
                                                <Grid item xs={12} sm={3}>
                                                    <TextField size="small" fullWidth label="Nombre" value={editingMember.full_name}
                                                        onChange={(e) => setEditingMember({ ...editingMember, full_name: e.target.value })} />
                                                </Grid>
                                                <Grid item xs={12} sm={2}>
                                                    <TextField size="small" fullWidth label="INE" value={editingMember.ine_key}
                                                        onChange={(e) => setEditingMember({ ...editingMember, ine_key: e.target.value })} />
                                                </Grid>
                                                <Grid item xs={12} sm={2}>
                                                    <TextField size="small" fullWidth label="Teléfono" value={editingMember.phone || ''}
                                                        onChange={(e) => setEditingMember({ ...editingMember, phone: e.target.value })} />
                                                </Grid>
                                                <Grid item xs={12} sm={2}>
                                                    <TextField size="small" fullWidth label="Email" value={editingMember.email || ''}
                                                        onChange={(e) => setEditingMember({ ...editingMember, email: e.target.value })} />
                                                </Grid>
                                                <Grid item xs={12} sm={3}>
                                                    <Button size="small" onClick={handleSaveEditedMember} disabled={loading}>Guardar</Button>
                                                    <Button size="small" onClick={() => setEditingMember(null)}>Cancelar</Button>
                                                </Grid>
                                            </Grid>
                                        ) : (
                                            <>
                                                <ListItemText
                                                    primary={member.full_name}
                                                    secondary={`INE: ${member.ine_key || '-'} | Tel: ${member.phone || '-'} | Sección: ${member.section_number || '-'}`}
                                                />
                                                <ListItemSecondaryAction>
                                                    <IconButton size="small" onClick={() => handleEditExisting(member)}><EditIcon fontSize="small" /></IconButton>
                                                    <IconButton size="small" color="error" onClick={() => handleDeleteExisting(member.id)}><DeleteIcon fontSize="small" /></IconButton>
                                                </ListItemSecondaryAction>
                                            </>
                                        )}
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Box>
                )}

                {/* Tab: Add New Members */}
                {tabValue === 1 && (
                    <form id="new-members-form" onSubmit={handleSubmitNew}>
                        <Typography variant="body2" color="text.secondary" mb={2}>
                            Espacios disponibles: {availableSlots - newMembers.length} de {availableSlots}
                        </Typography>
                        {newMembers.map((member, index) => (
                            <Box key={index} sx={{ mb: 2 }}>
                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                    <Typography variant="subtitle2" color="primary">Nuevo Miembro {index + 1}</Typography>
                                    {newMembers.length > 1 && (
                                        <IconButton size="small" onClick={() => removeNewMemberSlot(index)} disabled={loading}>
                                            <DeleteIcon fontSize="small" />
                                        </IconButton>
                                    )}
                                </Box>
                                <Grid container spacing={1}>
                                    <Grid item xs={12} sm={6}>
                                        <TextField fullWidth size="small" label="Nombre Completo *" value={member.full_name}
                                            onChange={(e) => handleNewMemberChange(index, 'full_name', e.target.value)} disabled={loading} />
                                    </Grid>
                                    <Grid item xs={12} sm={6}>
                                        <TextField fullWidth size="small" label="Clave de INE *" value={member.ine_key}
                                            onChange={(e) => handleNewMemberChange(index, 'ine_key', e.target.value)} disabled={loading} />
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                        <TextField fullWidth size="small" label="Teléfono" value={member.phone}
                                            onChange={(e) => handleNewMemberChange(index, 'phone', e.target.value)} disabled={loading} />
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                        <TextField fullWidth size="small" label="Email" type="email" value={member.email}
                                            onChange={(e) => handleNewMemberChange(index, 'email', e.target.value)} disabled={loading} />
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                        <TextField fullWidth size="small" label="Sección" value={member.section_number}
                                            onChange={(e) => handleNewMemberChange(index, 'section_number', e.target.value)} disabled={loading} />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth size="small" label="Referido por" value={member.referred_by}
                                            onChange={(e) => handleNewMemberChange(index, 'referred_by', e.target.value)} disabled={loading} />
                                    </Grid>
                                </Grid>
                                {index < newMembers.length - 1 && <Divider sx={{ mt: 2 }} />}
                            </Box>
                        ))}
                        {newMembers.length < availableSlots && (
                            <Button startIcon={<PersonAddIcon />} onClick={addNewMemberSlot} disabled={loading} fullWidth variant="outlined" sx={{ mt: 1 }}>
                                Agregar otro miembro
                            </Button>
                        )}
                    </form>
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose} disabled={loading} startIcon={<CancelIcon />}>Cerrar</Button>
                {tabValue === 1 && (
                    <Button type="submit" form="new-members-form" variant="contained" disabled={loading || success}
                        startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}>
                        {loading ? 'Guardando...' : 'Guardar Nuevos'}
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    )
}
