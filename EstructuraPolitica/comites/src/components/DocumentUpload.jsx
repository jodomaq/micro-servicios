/**
 * Componente para subir documentos y ver documentos existentes
 * Soporta captura de cámara en móvil
 */
import { useState, useEffect } from 'react'
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Alert,
    LinearProgress,
    Typography,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    IconButton,
    Tabs,
    Tab,
    Link,
    Chip,
} from '@mui/material'
import {
    CloudUpload as UploadIcon,
    Cancel as CancelIcon,
    InsertDriveFile as FileIcon,
    Delete as DeleteIcon,
    CameraAlt as CameraIcon,
    Image as ImageIcon,
    PictureAsPdf as PdfIcon,
    Download as DownloadIcon,
} from '@mui/icons-material'
import api from '../services/api'

const getFileIcon = (filename) => {
    if (!filename) return <FileIcon />
    const ext = filename.split('.').pop().toLowerCase()
    if (['jpg','jpeg','png','gif','webp','bmp'].includes(ext)) return <ImageIcon color="success" />
    if (ext === 'pdf') return <PdfIcon color="error" />
    return <FileIcon color="primary" />
}

export default function DocumentUpload({ open, onClose, onUpload, committeeId }) {
    const [files, setFiles] = useState([])
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(false)
    const [tabValue, setTabValue] = useState(0)
    const [existingDocs, setExistingDocs] = useState([])
    const [loadingDocs, setLoadingDocs] = useState(false)

    useEffect(() => {
        if (open && committeeId) {
            loadExistingDocs()
            setFiles([])
            setError(null)
            setSuccess(false)
            setProgress(0)
        }
    }, [open, committeeId])

    const loadExistingDocs = async () => {
        setLoadingDocs(true)
        try {
            const response = await api.get(`/committees/${committeeId}/documents`)
            setExistingDocs(response.data)
        } catch (err) {
            console.error('Error loading docs:', err)
        } finally {
            setLoadingDocs(false)
        }
    }

    const handleFileSelect = (e) => {
        const selectedFiles = Array.from(e.target.files)
        setFiles(prev => [...prev, ...selectedFiles])
        setError(null)
    }

    const handleRemoveFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index))
    }

    const handleDeleteExisting = async (docId) => {
        if (!window.confirm('¿Eliminar este documento?')) return
        try {
            await api.delete(`/committees/${committeeId}/documents/${docId}`)
            setExistingDocs(prev => prev.filter(d => d.id !== docId))
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar documento')
        }
    }

    const formatFileSize = (bytes) => {
        if (!bytes || bytes === 0) return '0 Bytes'
        const k = 1024
        const sizes = ['Bytes', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    }

    const handleUpload = async () => {
        if (files.length === 0) { setError('Seleccione al menos un archivo'); return }
        setUploading(true); setError(null); setSuccess(false); setProgress(0)
        try {
            for (let i = 0; i < files.length; i++) {
                const formData = new FormData()
                formData.append('file', files[i])
                await api.post(`/committees/${committeeId}/documents`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    onUploadProgress: (pe) => {
                        setProgress(Math.round(((i + pe.loaded / pe.total) / files.length) * 100))
                    },
                })
            }
            setSuccess(true)
            await loadExistingDocs()
            setTimeout(() => { onUpload(); handleClose() }, 1000)
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Error al subir'
            setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
        } finally {
            setUploading(false)
        }
    }

    const handleClose = () => {
        setFiles([]); setError(null); setSuccess(false); setProgress(0); onClose()
    }

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>Documentos del Comité</DialogTitle>
            <DialogContent>
                {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
                {success && <Alert severity="success" sx={{ mb: 2 }}>¡Documentos subidos exitosamente!</Alert>}

                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
                    <Tab label={`Existentes (${existingDocs.length})`} />
                    <Tab label="Subir Nuevos" />
                </Tabs>

                {tabValue === 0 && (
                    <Box>
                        {loadingDocs ? (
                            <Typography textAlign="center" py={2}>Cargando...</Typography>
                        ) : existingDocs.length === 0 ? (
                            <Typography color="text.secondary" textAlign="center" py={3}>No hay documentos</Typography>
                        ) : (
                            <List dense>
                                {existingDocs.map((doc) => (
                                    <ListItem key={doc.id} secondaryAction={
                                        <Box>
                                            {doc.file_url && (
                                                <IconButton edge="end" size="small" component="a" href={doc.file_url} target="_blank">
                                                    <DownloadIcon />
                                                </IconButton>
                                            )}
                                            <IconButton edge="end" size="small" color="error" onClick={() => handleDeleteExisting(doc.id)}>
                                                <DeleteIcon />
                                            </IconButton>
                                        </Box>
                                    }>
                                        <ListItemIcon>{getFileIcon(doc.file_name || doc.document_type)}</ListItemIcon>
                                        <ListItemText
                                            primary={doc.file_name || doc.document_type || 'Documento'}
                                            secondary={doc.created_at ? new Date(doc.created_at).toLocaleDateString() : ''}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Box>
                )}

                {tabValue === 1 && (
                    <Box>
                        <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <input accept="application/pdf,image/*,.doc,.docx,.xls,.xlsx" style={{ display: 'none' }} id="file-upload"
                                type="file" multiple onChange={handleFileSelect} disabled={uploading} />
                            <label htmlFor="file-upload">
                                <Button variant="outlined" component="span" startIcon={<UploadIcon />} disabled={uploading}>
                                    Seleccionar Archivos
                                </Button>
                            </label>
                            <input accept="image/*" capture="environment" style={{ display: 'none' }} id="camera-upload"
                                type="file" onChange={handleFileSelect} disabled={uploading} />
                            <label htmlFor="camera-upload">
                                <Button variant="outlined" component="span" startIcon={<CameraIcon />} disabled={uploading} color="secondary">
                                    Tomar Foto
                                </Button>
                            </label>
                        </Box>
                        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                            Formatos: PDF, imágenes, Word, Excel
                        </Typography>

                        {files.length > 0 && (
                            <Box>
                                <Typography variant="subtitle2" gutterBottom>Archivos seleccionados ({files.length}):</Typography>
                                <List dense>
                                    {files.map((file, index) => (
                                        <ListItem key={index} secondaryAction={
                                            <IconButton edge="end" onClick={() => handleRemoveFile(index)} disabled={uploading} size="small"><DeleteIcon /></IconButton>
                                        }>
                                            <ListItemIcon>{getFileIcon(file.name)}</ListItemIcon>
                                            <ListItemText primary={file.name} secondary={formatFileSize(file.size)} />
                                            {file.type?.startsWith('image/') && (
                                                <Box component="img" src={URL.createObjectURL(file)} sx={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 1, mr: 1 }} />
                                            )}
                                        </ListItem>
                                    ))}
                                </List>
                            </Box>
                        )}

                        {uploading && (
                            <Box sx={{ mt: 2 }}>
                                <LinearProgress variant="determinate" value={progress} />
                                <Typography variant="caption" display="block" align="center" sx={{ mt: 1 }}>Subiendo... {progress}%</Typography>
                            </Box>
                        )}
                    </Box>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={uploading} startIcon={<CancelIcon />}>Cerrar</Button>
                {tabValue === 1 && (
                    <Button onClick={handleUpload} variant="contained" disabled={uploading || files.length === 0 || success} startIcon={<UploadIcon />}>
                        {uploading ? 'Subiendo...' : 'Subir'}
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    )
}
