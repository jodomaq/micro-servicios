/**
 * Dashboard principal - vista de resumen
 */
import { useState, useEffect } from 'react'
import { Grid, Paper, Typography, Box, CircularProgress } from '@mui/material'
import { People, Group, Event, Poll, AccountTree, AssignmentInd } from '@mui/icons-material'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../services/api'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658']

const StatCard = ({ title, value, icon: Icon, color, loading }) => (
    <Paper sx={{ p: 3, height: '100%' }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
                {loading ? (
                    <CircularProgress size={32} />
                ) : (
                    <>
                        <Typography variant="h4" fontWeight="bold">
                            {value}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {title}
                        </Typography>
                    </>
                )}
            </Box>
            <Box
                sx={{
                    backgroundColor: `${color}.lighter`,
                    borderRadius: 2,
                    p: 1.5,
                }}
            >
                <Icon sx={{ color: `${color}.main`, fontSize: 32 }} />
            </Box>
        </Box>
    </Paper>
)

export default function DashboardPage() {
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState({
        committees: 0,
        members: 0,
        units: 0,
        users: 0,
    })
    const [committeesByType, setCommitteesByType] = useState([])
    const [committeesByUnit, setCommitteesByUnit] = useState([])
    const [membersByCommittee, setMembersByCommittee] = useState([])

    useEffect(() => {
        loadDashboardData()
    }, [])

    const loadDashboardData = async () => {
        setLoading(true)
        try {
            // Cargar comités
            const committeesRes = await api.get('/committees')
            const committees = committeesRes.data

            // Cargar unidades administrativas
            const unitsRes = await api.get('/administrative-units')
            const units = unitsRes.data

            // Cargar usuarios
            const usersRes = await api.get('/users')
            const users = usersRes.data

            // Cargar tipos de comités
            const typesRes = await api.get('/committee-types')
            const types = typesRes.data

            // Calcular estadísticas
            const totalMembers = committees.reduce((sum, c) => sum + (c.member_count || 0), 0)

            setStats({
                committees: committees.length,
                members: totalMembers,
                units: units.length,
                users: users.length,
            })

            // Comités por tipo
            const typeStats = types.map(type => {
                const count = committees.filter(c => c.committee_type_id === type.id).length
                return {
                    name: type.name,
                    value: count
                }
            }).filter(t => t.value > 0)
            setCommitteesByType(typeStats)

            // Comités por unidad administrativa (top 10)
            const unitCounts = {}
            committees.forEach(c => {
                if (c.administrative_unit) {
                    const unitName = c.administrative_unit.name
                    unitCounts[unitName] = (unitCounts[unitName] || 0) + 1
                }
            })
            const unitStats = Object.entries(unitCounts)
                .map(([name, count]) => ({ name, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 10)
            setCommitteesByUnit(unitStats)

            // Top 10 comités por cantidad de miembros
            const memberStats = committees
                .map(c => ({
                    name: c.name.length > 20 ? c.name.substring(0, 20) + '...' : c.name,
                    members: c.member_count || 0
                }))
                .sort((a, b) => b.members - a.members)
                .slice(0, 10)
            setMembersByCommittee(memberStats)

        } catch (error) {
            console.error('Error al cargar datos del dashboard:', error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold">
                Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
                Resumen de actividades y estadísticas del sistema
            </Typography>

            {/* Cards de estadísticas */}
            <Grid container spacing={3} sx={{ mt: 2 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Comités"
                        value={stats.committees}
                        icon={Group}
                        color="primary"
                        loading={loading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Integrantes"
                        value={stats.members}
                        icon={People}
                        color="secondary"
                        loading={loading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Unidades"
                        value={stats.units}
                        icon={AccountTree}
                        color="success"
                        loading={loading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Usuarios"
                        value={stats.users}
                        icon={AssignmentInd}
                        color="info"
                        loading={loading}
                    />
                </Grid>
            </Grid>

            {/* Gráficas */}
            <Grid container spacing={3} sx={{ mt: 2 }}>
                {/* Gráfica de Tipos de Comités */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Distribución por Tipo de Comité
                        </Typography>
                        {loading ? (
                            <Box display="flex" justifyContent="center" p={4}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={committeesByType}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="value"
                                    >
                                        {committeesByType.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        )}
                    </Paper>
                </Grid>

                {/* Gráfica de Miembros por Comité */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Top 10 Comités por Número de Miembros
                        </Typography>
                        {loading ? (
                            <Box display="flex" justifyContent="center" p={4}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={membersByCommittee}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="members" fill="#8884d8" name="Miembros" />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </Paper>
                </Grid>

                {/* Gráfica de Comités por Unidad Administrativa */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Comités por Unidad Administrativa (Top 10)
                        </Typography>
                        {loading ? (
                            <Box display="flex" justifyContent="center" p={4}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={committeesByUnit} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" />
                                    <YAxis dataKey="name" type="category" width={150} />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="count" fill="#00C49F" name="Comités" />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    )
}
