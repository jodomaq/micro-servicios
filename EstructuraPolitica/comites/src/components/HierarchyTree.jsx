/**
 * Árbol jerárquico de unidades administrativas
 * Con contadores recursivos de comités, miembros y usuarios por nivel
 */
import { useState, useEffect } from 'react'
import {
    Box,
    Paper,
    Typography,
    CircularProgress,
    Alert,
    IconButton,
    Collapse,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Chip,
    TextField,
    MenuItem,
    Stack,
} from '@mui/material'
import {
    ExpandMore as ExpandMoreIcon,
    ChevronRight as ChevronRightIcon,
    AccountBalance as StateIcon,
    LocationOn as LocationIcon,
    Place as PlaceIcon,
    HowToVote as VoteIcon,
    Groups as GroupsIcon,
    People as PeopleIcon,
} from '@mui/icons-material'
import api from '../services/api'

const UNIT_TYPE_ICONS = {
    STATE: StateIcon,
    REGION: LocationIcon,
    DISTRICT: PlaceIcon,
    MUNICIPALITY: PlaceIcon,
    SECTION: VoteIcon,
}

const UNIT_TYPE_COLORS = {
    STATE: 'error',
    REGION: 'warning',
    DISTRICT: 'info',
    MUNICIPALITY: 'success',
    SECTION: 'default',
}

const UNIT_TYPE_LABELS = {
    STATE: 'Estado',
    REGION: 'Región',
    DISTRICT: 'Distrito',
    MUNICIPALITY: 'Municipio',
    SECTION: 'Sección',
}

function TreeNode({ unit, children, level = 0, stats }) {
    const [expanded, setExpanded] = useState(level < 2)

    const hasChildren = children && children.length > 0
    const Icon = UNIT_TYPE_ICONS[unit.unit_type] || LocationIcon
    const nodeStats = stats?.[unit.id]

    return (
        <Box>
            <ListItem
                disablePadding
                sx={{
                    pl: level * 3,
                    borderLeft: level > 0 ? '2px solid #e0e0e0' : 'none',
                }}
            >
                {hasChildren && (
                    <IconButton size="small" onClick={() => setExpanded(!expanded)} sx={{ mr: 1 }}>
                        {expanded ? <ExpandMoreIcon /> : <ChevronRightIcon />}
                    </IconButton>
                )}
                {!hasChildren && <Box sx={{ width: 40 }} />}

                <ListItemButton onClick={() => hasChildren && setExpanded(!expanded)} sx={{ borderRadius: 1 }}>
                    <ListItemIcon>
                        <Icon color={UNIT_TYPE_COLORS[unit.unit_type]} />
                    </ListItemIcon>
                    <ListItemText
                        primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                                <Typography variant="body1">{unit.name}</Typography>
                                {unit.code && <Typography variant="caption" color="text.secondary">({unit.code})</Typography>}
                                {nodeStats && (
                                    <Stack direction="row" spacing={0.5} sx={{ ml: 1 }}>
                                        <Chip icon={<GroupsIcon sx={{ fontSize: 14 }} />} label={nodeStats.committee_count ?? 0} size="small" color="primary" variant="outlined" sx={{ height: 22 }} />
                                        <Chip icon={<PeopleIcon sx={{ fontSize: 14 }} />} label={nodeStats.member_count ?? 0} size="small" color="success" variant="outlined" sx={{ height: 22 }} />
                                    </Stack>
                                )}
                            </Box>
                        }
                        secondary={
                            <Chip label={UNIT_TYPE_LABELS[unit.unit_type]} size="small" color={UNIT_TYPE_COLORS[unit.unit_type]} variant="outlined" sx={{ mt: 0.5 }} />
                        }
                    />
                </ListItemButton>
            </ListItem>

            {hasChildren && (
                <Collapse in={expanded} timeout="auto" unmountOnExit>
                    <List disablePadding>
                        {children.map((child) => (
                            <TreeNode key={child.id} unit={child} children={child.children} level={level + 1} stats={stats} />
                        ))}
                    </List>
                </Collapse>
            )}
        </Box>
    )
}

export default function HierarchyTree() {
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [hierarchyData, setHierarchyData] = useState([])
    const [stats, setStats] = useState({})
    const [filterType, setFilterType] = useState('')

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        setLoading(true)
        setError(null)
        try {
            const [treeRes, statsRes] = await Promise.all([
                api.get('/administrative-units/tree'),
                api.get('/dashboard/tree-stats').catch(() => ({ data: [] })),
            ])
            setHierarchyData(treeRes.data)
            // Index stats by unit id
            const statsMap = {}
            const indexStats = (nodes) => {
                if (!Array.isArray(nodes)) return
                for (const n of nodes) {
                    statsMap[n.id] = n
                    if (n.children) indexStats(n.children)
                }
            }
            indexStats(statsRes.data)
            setStats(statsMap)
        } catch (err) {
            const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar la jerarquía'
            setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
        } finally {
            setLoading(false)
        }
    }

    // Filter tree by unit_type
    const filterTree = (nodes) => {
        if (!filterType) return nodes
        return nodes.reduce((acc, node) => {
            if (node.unit_type === filterType) {
                acc.push({ ...node, children: node.children ? filterTree(node.children) : [] })
            } else if (node.children) {
                const filtered = filterTree(node.children)
                if (filtered.length > 0) acc.push({ ...node, children: filtered })
            }
            return acc
        }, [])
    }

    const displayData = filterTree(hierarchyData)

    if (loading) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress /></Box>
    }
    if (error) {
        return <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>
    }
    if (hierarchyData.length === 0) {
        return <Paper sx={{ p: 3, textAlign: 'center' }}><Typography color="text.secondary">No hay unidades administrativas configuradas</Typography></Paper>
    }

    return (
        <Paper>
            <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                <Box>
                    <Typography variant="h6">Estructura Administrativa</Typography>
                    <Typography variant="caption" color="text.secondary">Haga clic para expandir/contraer niveles</Typography>
                </Box>
                <TextField
                    select size="small" label="Filtrar por tipo" value={filterType}
                    onChange={(e) => setFilterType(e.target.value)} sx={{ minWidth: 180 }}
                >
                    <MenuItem value="">Todos</MenuItem>
                    {Object.entries(UNIT_TYPE_LABELS).map(([k, v]) => (
                        <MenuItem key={k} value={k}>{v}</MenuItem>
                    ))}
                </TextField>
            </Box>
            <List sx={{ p: 0 }}>
                {displayData.map((unit) => (
                    <TreeNode key={unit.id} unit={unit} children={unit.children} level={0} stats={stats} />
                ))}
            </List>
        </Paper>
    )
}
