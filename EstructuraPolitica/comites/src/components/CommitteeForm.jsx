/**
 * Formulario para crear/editar comités
 * Usa React Hook Form + Yup para validación
 */
import { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Grid,
    MenuItem,
    Box,
    Alert,
    CircularProgress,
} from '@mui/material'
import { Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material'
import api from '../services/api'

const committeeSchema = yup.object().shape({
    name: yup.string().required('El nombre del comité es requerido').min(3, 'Mínimo 3 caracteres'),
    section_number: yup.string().nullable(),
    committee_type_id: yup.number().required('Seleccione un tipo de comité').typeError('Seleccione un tipo de comité'),
    administrative_unit_id: yup.number().required('Seleccione una unidad administrativa').typeError('Seleccione una unidad administrativa'),
    president_name: yup.string().required('El nombre del presidente es requerido').min(3, 'Mínimo 3 caracteres'),
    president_email: yup.string().email('Email inválido').nullable().transform((v) => v === '' ? null : v),
    president_phone: yup.string()
        .matches(/^[\d\s+()-]{7,20}$/, { message: 'Teléfono inválido', excludeEmptyString: true })
        .nullable()
        .transform((v) => v === '' ? null : v),
    president_affiliation_key: yup.string().nullable().transform((v) => v === '' ? null : v),
})

export default function CommitteeForm({ open, onClose, onSave, committee = null }) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [committeeTypes, setCommitteeTypes] = useState([])
    const [administrativeUnits, setAdministrativeUnits] = useState([])

    const { control, handleSubmit, reset, formState: { errors } } = useForm({
        resolver: yupResolver(committeeSchema),
        defaultValues: {
            name: '', section_number: '', committee_type_id: '', administrative_unit_id: '',
            president_name: '', president_email: '', president_phone: '', president_affiliation_key: '',
        }
    })

    useEffect(() => {
        if (open) {
            loadCommitteeTypes()
            loadAdministrativeUnits()
            if (committee) {
                reset({
                    name: committee.name || '',
                    section_number: committee.section_number || '',
                    committee_type_id: committee.committee_type?.id || committee.committee_type_id || '',
                    administrative_unit_id: committee.administrative_unit?.id || committee.administrative_unit_id || '',
                    president_name: committee.president_name || '',
                    president_email: committee.president_email || '',
                    president_phone: committee.president_phone || '',
                    president_affiliation_key: committee.president_affiliation_key || '',
                })
            } else {
                reset({ name: '', section_number: '', committee_type_id: '', administrative_unit_id: '',
                    president_name: '', president_email: '', president_phone: '', president_affiliation_key: '' })
            }
            setError(null)
        }
    }, [open, committee, reset])

    const loadCommitteeTypes = async () => {
        try { setCommitteeTypes((await api.get('/committee-types')).data) } catch (err) { console.error(err) }
    }
    const loadAdministrativeUnits = async () => {
        try { setAdministrativeUnits((await api.get('/administrative-units')).data) } catch (err) { console.error(err) }
    }

    const onSubmit = async (data) => {
        setLoading(true); setError(null)
        const cleanData = { ...data }
        cleanData.committee_type_id = Number(cleanData.committee_type_id)
        cleanData.administrative_unit_id = Number(cleanData.administrative_unit_id)
        try {
            const response = committee?.id
                ? await api.put(`/committees/${committee.id}`, cleanData)
                : await api.post('/committees', cleanData)
            onSave(response.data); onClose()
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Error al guardar'
            setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
        } finally { setLoading(false) }
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>{committee?.id ? 'Editar Comité' : 'Nuevo Comité'}</DialogTitle>
            <form onSubmit={handleSubmit(onSubmit)}>
                <DialogContent>
                    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <Controller name="name" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Nombre del Comité" error={!!errors.name} helperText={errors.name?.message} disabled={loading} />
                            )} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="committee_type_id" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth select label="Tipo de Comité" error={!!errors.committee_type_id} helperText={errors.committee_type_id?.message} disabled={loading}>
                                    {committeeTypes.map((t) => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
                                </TextField>
                            )} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="administrative_unit_id" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth select label="Unidad Administrativa" error={!!errors.administrative_unit_id} helperText={errors.administrative_unit_id?.message} disabled={loading}>
                                    {administrativeUnits.map((u) => <MenuItem key={u.id} value={u.id}>{u.name} ({u.unit_type})</MenuItem>)}
                                </TextField>
                            )} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="section_number" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Número de Sección" disabled={loading} />
                            )} />
                        </Grid>
                        <Grid item xs={12}><Box sx={{ mt: 2, mb: 1 }}><strong>Información del Presidente</strong></Box></Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="president_name" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Nombre del Presidente" error={!!errors.president_name} helperText={errors.president_name?.message} disabled={loading} />
                            )} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="president_email" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth type="email" label="Email del Presidente" error={!!errors.president_email} helperText={errors.president_email?.message} disabled={loading} />
                            )} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="president_phone" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Teléfono del Presidente" error={!!errors.president_phone} helperText={errors.president_phone?.message} disabled={loading} />
                            )} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Controller name="president_affiliation_key" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Clave de Afiliación" disabled={loading} />
                            )} />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={onClose} disabled={loading} startIcon={<CancelIcon />}>Cancelar</Button>
                    <Button type="submit" variant="contained" disabled={loading} startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}>
                        {loading ? 'Guardando...' : 'Guardar'}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    )
}
