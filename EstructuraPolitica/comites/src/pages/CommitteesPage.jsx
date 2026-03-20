/**
 * Página de gestión de comités (INTEGRADA CON BACKEND)
 */
import { useState, useEffect } from 'react'
import {
    Container,
    Typography,
    Button,
    Box,
    Alert,
    Snackbar,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import CommitteeForm from '../components/CommitteeForm'
import CommitteeList from '../components/CommitteeList'
import MemberForm from '../components/MemberForm'
import DocumentUpload from '../components/DocumentUpload'
import api from '../services/api'

export default function CommitteesPage() {
    const { user } = useAuth()
    const [committees, setCommittees] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    
    // Modales
    const [committeeFormOpen, setCommitteeFormOpen] = useState(false)
    const [memberFormOpen, setMemberFormOpen] = useState(false)
    const [documentUploadOpen, setDocumentUploadOpen] = useState(false)
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
    
    // Estados
    const [selectedCommittee, setSelectedCommittee] = useState(null)
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' })

    useEffect(() => {
        loadCommittees()
    }, [])

    const loadCommittees = async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await api.get('/committees')
            setCommittees(response.data)
        } catch (err) {
            const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar los comités'
            setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
        } finally {
            setLoading(false)
        }
    }

    const handleCreateCommittee = () => {
        setSelectedCommittee(null)
        setCommitteeFormOpen(true)
    }

    const handleEditCommittee = (committee) => {
        setSelectedCommittee(committee)
        setCommitteeFormOpen(true)
    }

    const handleDeleteCommittee = (committee) => {
        setSelectedCommittee(committee)
        setDeleteDialogOpen(true)
    }

    const confirmDelete = async () => {
        try {
            await api.delete(`/committees/${selectedCommittee.id}`)
            setSnackbar({
                open: true,
                message: 'Comité eliminado exitosamente',
                severity: 'success'
            })
            loadCommittees()
        } catch (err) {
            setSnackbar({
                open: true,
                message: err.response?.data?.detail || 'Error al eliminar el comité',
                severity: 'error'
            })
        } finally {
            setDeleteDialogOpen(false)
            setSelectedCommittee(null)
        }
    }

    const handleViewMembers = (committee) => {
        setSelectedCommittee(committee)
        setMemberFormOpen(true)
    }

    const handleViewDocuments = (committee) => {
        setSelectedCommittee(committee)
        setDocumentUploadOpen(true)
    }

    const handleCommitteeSaved = () => {
        setSnackbar({
            open: true,
            message: selectedCommittee ? 'Comité actualizado exitosamente' : 'Comité creado exitosamente',
            severity: 'success'
        })
        loadCommittees()
    }

    const handleMembersSaved = () => {
        setSnackbar({
            open: true,
            message: 'Miembros agregados exitosamente',
            severity: 'success'
        })
        loadCommittees()
    }

    const handleDocumentsUploaded = () => {
        setSnackbar({
            open: true,
            message: 'Documentos subidos exitosamente',
            severity: 'success'
        })
        loadCommittees()
    }

    return (
        <Container maxWidth="xl">
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <Typography variant="h4" gutterBottom>
                        Comités
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Gestione los comités de su organización
                    </Typography>
                </div>

                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleCreateCommittee}
                    disabled={loading}
                >
                    Nuevo Comité
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            <CommitteeList
                committees={committees}
                onEdit={handleEditCommittee}
                onDelete={handleDeleteCommittee}
                onViewMembers={handleViewMembers}
                onViewDocuments={handleViewDocuments}
                loading={loading}
            />

            {/* Modal: Formulario de Comité */}
            <CommitteeForm
                open={committeeFormOpen}
                onClose={() => {
                    setCommitteeFormOpen(false)
                    setSelectedCommittee(null)
                }}
                onSave={handleCommitteeSaved}
                committee={selectedCommittee}
                tenantId={user?.tenant_id}
            />

            {/* Modal: Formulario de Miembros */}
            <MemberForm
                open={memberFormOpen}
                onClose={() => {
                    setMemberFormOpen(false)
                    setSelectedCommittee(null)
                }}
                onSave={handleMembersSaved}
                committeeId={selectedCommittee?.id}
            />

            {/* Modal: Subir Documentos */}
            <DocumentUpload
                open={documentUploadOpen}
                onClose={() => {
                    setDocumentUploadOpen(false)
                    setSelectedCommittee(null)
                }}
                onUpload={handleDocumentsUploaded}
                committeeId={selectedCommittee?.id}
            />

            {/* Modal: Confirmar Eliminación */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    ¿Está seguro de que desea eliminar el comité "{selectedCommittee?.name}"?
                    Esta acción no se puede deshacer.
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>
                        Cancelar
                    </Button>
                    <Button onClick={confirmDelete} color="error" variant="contained">
                        Eliminar
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar para notificaciones */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={4000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert
                    onClose={() => setSnackbar({ ...snackbar, open: false })}
                    severity={snackbar.severity}
                    sx={{ width: '100%' }}
                >
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Container>
    )
}
