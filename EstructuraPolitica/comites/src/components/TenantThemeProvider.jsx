/**
 * Theme Provider dinámico basado en colores del tenant
 * Aplica branding personalizado (logo, colores) automáticamente
 */
import { createTheme, ThemeProvider } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import { useTenant } from '../contexts/TenantContext'

export const TenantThemeProvider = ({ children }) => {
    const { tenant } = useTenant()

    const theme = createTheme({
        palette: {
            mode: 'light',
            primary: {
                main: tenant?.primary_color || '#1976d2',
            },
            secondary: {
                main: tenant?.secondary_color || '#dc004e',
            },
        },
        typography: {
            fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        },
        components: {
            MuiButton: {
                styleOverrides: {
                    root: {
                        textTransform: 'none',
                        borderRadius: 8,
                    },
                },
            },
            MuiCard: {
                styleOverrides: {
                    root: {
                        borderRadius: 12,
                    },
                },
            },
        },
    })

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    )
}
