/**
 * Página de visualización de jerarquía administrativa (INTEGRADA CON BACKEND)
 */
import { Container, Typography, Box } from '@mui/material'
import HierarchyTree from '../components/HierarchyTree'

export default function HierarchyPage() {
    return (
        <Container maxWidth="xl">
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Jerarquía Administrativa
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Visualice la estructura organizacional de unidades administrativas
                </Typography>
            </Box>

            <HierarchyTree />
        </Container>
    )
}
