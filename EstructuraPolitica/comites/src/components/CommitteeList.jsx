/**
 * Lista de comités con tabla (desktop) y tarjetas (mobile)
 */
import { useState } from 'react'
import {
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    IconButton,
    Chip,
    Box,
    TextField,
    InputAdornment,
    Tooltip,
    Card,
    CardContent,
    CardActions,
    Typography,
    Grid,
    useMediaQuery,
    useTheme,
} from '@mui/material'
import {
    Edit as EditIcon,
    Delete as DeleteIcon,
    People as PeopleIcon,
    Search as SearchIcon,
    Attachment as AttachmentIcon,
} from '@mui/icons-material'

export default function CommitteeList({ 
    committees, 
    onEdit, 
    onDelete, 
    onViewMembers,
    onViewDocuments,
    loading = false 
}) {
    const [page, setPage] = useState(0)
    const [rowsPerPage, setRowsPerPage] = useState(10)
    const [searchTerm, setSearchTerm] = useState('')
    const theme = useTheme()
    const isMobile = useMediaQuery(theme.breakpoints.down('md'))

    const filteredCommittees = committees.filter(committee => {
        const search = searchTerm.toLowerCase()
        return (
            committee.name?.toLowerCase().includes(search) ||
            committee.president_name?.toLowerCase().includes(search) ||
            committee.section_number?.toLowerCase().includes(search) ||
            committee.committee_type?.name?.toLowerCase().includes(search)
        )
    })

    const paginatedCommittees = filteredCommittees.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

    return (
        <Paper>
            <Box sx={{ p: 2 }}>
                <TextField
                    fullWidth placeholder="Buscar por nombre, presidente, sección..." value={searchTerm}
                    onChange={(e) => { setSearchTerm(e.target.value); setPage(0) }}
                    InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
                />
            </Box>

            {isMobile ? (
                /* Mobile: Card View */
                <Box sx={{ p: 2 }}>
                    {loading ? (
                        <Typography textAlign="center" py={3}>Cargando...</Typography>
                    ) : paginatedCommittees.length === 0 ? (
                        <Typography textAlign="center" color="text.secondary" py={3}>
                            {searchTerm ? 'No se encontraron comités' : 'No hay comités registrados'}
                        </Typography>
                    ) : (
                        <Grid container spacing={2}>
                            {paginatedCommittees.map((committee) => (
                                <Grid item xs={12} sm={6} key={committee.id}>
                                    <Card variant="outlined">
                                        <CardContent sx={{ pb: 1 }}>
                                            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                                                {committee.name}
                                            </Typography>
                                            <Box display="flex" gap={1} flexWrap="wrap" mb={1}>
                                                <Chip label={committee.committee_type?.name || 'N/A'} size="small" color="primary" variant="outlined" />
                                                {committee.section_number && <Chip label={`S: ${committee.section_number}`} size="small" />}
                                                <Chip label={`${committee.members_count || 0} miembros`} size="small" color="info" variant="outlined" />
                                            </Box>
                                            <Typography variant="body2" color="text.secondary">
                                                Presidente: {committee.president_name}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                {committee.administrative_unit?.name || ''}
                                            </Typography>
                                        </CardContent>
                                        <CardActions sx={{ justifyContent: 'flex-end' }}>
                                            <Tooltip title="Miembros"><IconButton size="small" color="primary" onClick={() => onViewMembers(committee)}><PeopleIcon /></IconButton></Tooltip>
                                            <Tooltip title="Documentos"><IconButton size="small" color="info" onClick={() => onViewDocuments(committee)}><AttachmentIcon /></IconButton></Tooltip>
                                            <Tooltip title="Editar"><IconButton size="small" color="primary" onClick={() => onEdit(committee)}><EditIcon /></IconButton></Tooltip>
                                            <Tooltip title="Eliminar"><IconButton size="small" color="error" onClick={() => onDelete(committee)}><DeleteIcon /></IconButton></Tooltip>
                                        </CardActions>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>
                    )}
                </Box>
            ) : (
                /* Desktop: Table View */
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Nombre</TableCell>
                                <TableCell>Tipo</TableCell>
                                <TableCell>Sección</TableCell>
                                <TableCell>Presidente</TableCell>
                                <TableCell>Unidad Administrativa</TableCell>
                                <TableCell>Miembros</TableCell>
                                <TableCell align="right">Acciones</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loading ? (
                                <TableRow><TableCell colSpan={7} align="center">Cargando...</TableCell></TableRow>
                            ) : paginatedCommittees.length === 0 ? (
                                <TableRow><TableCell colSpan={7} align="center">{searchTerm ? 'No se encontraron comités' : 'No hay comités registrados'}</TableCell></TableRow>
                            ) : (
                                paginatedCommittees.map((committee) => (
                                    <TableRow key={committee.id} hover>
                                        <TableCell>{committee.name}</TableCell>
                                        <TableCell><Chip label={committee.committee_type?.name || 'N/A'} size="small" color="primary" variant="outlined" /></TableCell>
                                        <TableCell>{committee.section_number || '-'}</TableCell>
                                        <TableCell>{committee.president_name}</TableCell>
                                        <TableCell>{committee.administrative_unit?.name || 'N/A'}</TableCell>
                                        <TableCell><Chip label={committee.members_count || 0} size="small" /></TableCell>
                                        <TableCell align="right">
                                            <Tooltip title="Ver miembros"><IconButton size="small" color="primary" onClick={() => onViewMembers(committee)}><PeopleIcon /></IconButton></Tooltip>
                                            <Tooltip title="Ver documentos"><IconButton size="small" color="info" onClick={() => onViewDocuments(committee)}><AttachmentIcon /></IconButton></Tooltip>
                                            <Tooltip title="Editar"><IconButton size="small" color="primary" onClick={() => onEdit(committee)}><EditIcon /></IconButton></Tooltip>
                                            <Tooltip title="Eliminar"><IconButton size="small" color="error" onClick={() => onDelete(committee)}><DeleteIcon /></IconButton></Tooltip>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            <TablePagination
                component="div" count={filteredCommittees.length} page={page}
                onPageChange={(_, p) => setPage(p)} rowsPerPage={rowsPerPage}
                onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0) }}
                rowsPerPageOptions={[5, 10, 25, 50]} labelRowsPerPage="Filas por página:"
            />
        </Paper>
    )
}
