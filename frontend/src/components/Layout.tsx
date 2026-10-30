import LockOutlined from '@mui/icons-material/LockOutlined'
import PublicOutlined from '@mui/icons-material/PublicOutlined'
import { Alert, AppBar, Box, Button, Chip, Container, Link, Toolbar, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink, Outlet } from 'react-router-dom'
import { api } from '../api'

export default function Layout() {
  const [demo, setDemo] = useState(false)
  useEffect(() => {
    api.status().then((s) => setDemo(s.demo)).catch(() => {})
  }, [])

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
            icon={demo ? <PublicOutlined sx={{ color: 'inherit !important' }} /> : <LockOutlined sx={{ color: 'inherit !important' }} />}
            label={demo ? 'Public demo' : 'Offline'}
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
        {demo && (
          <Alert severity="warning" className="no-print" sx={{ mb: 3 }}>
            <b>This is a public demo server, with a sample story and test photos.</b> Please don't upload real family
            recordings or photos: anyone can see them here. The real Ebyafaayo runs on your own computer, with no internet.
            To try Gemma, open <Link component={RouterLink} to="/recordings/1">the sample story's transcript</Link> and press “Turn into a
            family memory” (about 3 to 4 minutes), or add a photo on <Link component={RouterLink} to="/people/1">Nalongo's page</Link>.
            The speech model is not installed here, so new recordings need a typed transcript.{' '}
            <Link href="https://github.com/Nuwahereza-eng/ebyafaayo">Run it at home</Link>.
          </Alert>
        )}
        <Outlet />
      </Container>
      <Box component="footer" className="no-print" sx={{ py: 2, textAlign: 'center', color: 'text.secondary', fontSize: 13 }}>
        {demo
          ? 'Public demo: the stories here are samples. At home, Ebyafaayo keeps everything on your own computer.'
          : "Your family's stories stay on this computer. Nothing is sent to the internet."}
      </Box>
    </Box>
  )
}
