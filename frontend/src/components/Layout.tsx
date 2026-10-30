import LockOutlined from '@mui/icons-material/LockOutlined'
import { AppBar, Box, Button, Chip, Container, Toolbar, Typography } from '@mui/material'
import { Link as RouterLink, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="sticky" elevation={0} className="no-print" sx={{ bgcolor: 'primary.main' }}>
        <Toolbar sx={{ gap: 1, flexWrap: 'wrap' }}>
          <Typography
            component={RouterLink}
            to="/"
            variant="h6"
            sx={{ color: 'inherit', textDecoration: 'none', mr: 'auto', fontSize: { xs: '1.1rem', sm: '1.3rem' } }}
          >
            Ebyafaayo
          </Typography>
          <Button color="inherit" component={RouterLink} to="/book">
            Memory book
          </Button>
          <Button color="inherit" component={RouterLink} to="/about">
            About
          </Button>
          <Chip
            icon={<LockOutlined sx={{ color: 'inherit !important' }} />}
            label="Offline"
            size="small"
            component={RouterLink}
            to="/about"
            clickable
            sx={{ color: 'inherit', borderColor: 'rgba(255,255,255,0.5)', display: { xs: 'none', sm: 'flex' } }}
            variant="outlined"
          />
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ py: { xs: 2, sm: 4 }, flex: 1 }}>
        <Outlet />
      </Container>
      <Box component="footer" className="no-print" sx={{ py: 2, textAlign: 'center', color: 'text.secondary', fontSize: 13 }}>
        Your family's stories stay on this computer. Nothing is sent to the internet.
      </Box>
    </Box>
  )
}
