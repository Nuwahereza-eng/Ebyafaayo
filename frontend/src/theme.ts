import { createTheme } from '@mui/material/styles'

export const SERIF = '"Lora", Georgia, serif'

export const theme = createTheme({
  palette: {
    primary: { main: '#6D4C41' }, // bark cloth
    secondary: { main: '#1B5E20' }, // banana leaf
    background: { default: '#FBF7F0', paper: '#FFFDF9' },
    text: { primary: '#2E2420', secondary: '#6B5D55' },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter", system-ui, sans-serif',
    h1: { fontFamily: SERIF, fontWeight: 600 },
    h2: { fontFamily: SERIF, fontWeight: 600 },
    h3: { fontFamily: SERIF, fontWeight: 600 },
    h4: { fontFamily: SERIF, fontWeight: 600 },
    h5: { fontFamily: SERIF, fontWeight: 600 },
    h6: { fontFamily: SERIF, fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiCard: { defaultProps: { variant: 'outlined' } },
    MuiTooltip: {
      styleOverrides: { tooltip: { fontSize: '0.9rem', fontFamily: SERIF, maxWidth: 360, lineHeight: 1.5 } },
    },
  },
})
