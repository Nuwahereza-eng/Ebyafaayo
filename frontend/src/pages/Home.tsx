import Mic from '@mui/icons-material/Mic'
import { Alert, Avatar, Box, Button, Card, CardActionArea, CardContent, Skeleton, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { api, type Person, type Status } from '../api'

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('')
}

export function ModelStatus({ status }: { status: Status | null }) {
  if (!status) return null
  const problems = []
  if (!status.asr.ready) problems.push('The Luganda speech model is not installed yet, so you can type transcripts by hand for now.')
  if (!status.gemma.running) problems.push('Ollama is not running, so Gemma cannot write memories. Start it with "ollama serve".')
  else if (!status.gemma.model_ready) problems.push(`Gemma (${status.gemma.model}) is not downloaded yet. Run "ollama pull ${status.gemma.model}".`)
  if (!problems.length) return null
  return (
    <Alert severity="info" sx={{ mb: 3 }}>
      {problems.map((p) => (
        <div key={p}>{p}</div>
      ))}
    </Alert>
  )
}

export default function Home() {
  const [people, setPeople] = useState<Person[] | null>(null)
  const [status, setStatus] = useState<Status | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.people().then(setPeople).catch((e) => setError(e.message))
    api.status().then(setStatus).catch(() => {})
  }, [])

  return (
    <Box>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontSize: { xs: '2rem', sm: '2.8rem' }, mb: 1 }}>
          Ebyafaayo
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 520, mx: 'auto', mb: 3 }}>
          Record our elders telling their stories in their own words, and keep them as a family memory book.
        </Typography>
        <Button variant="contained" size="large" startIcon={<Mic />} component={RouterLink} to="/record" sx={{ px: 4, py: 1.5 }}>
          Record a new story
        </Button>
      </Box>

      <ModelStatus status={status} />
      {error && <Alert severity="error">{error}</Alert>}

      <Typography variant="h5" component="h2" sx={{ mb: 2 }}>
        Our elders and ancestors
      </Typography>
      {people === null && !error && <Skeleton variant="rounded" height={120} />}
      {people?.length === 0 && (
        <Typography color="text.secondary">
          No stories yet. Start by recording an elder: Jjajja, a parent, an aunt or uncle.
        </Typography>
      )}
      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' } }}>
        {people?.map((p) => (
          <Card key={p.id}>
            <CardActionArea component={RouterLink} to={`/people/${p.id}`} sx={{ height: '100%' }}>
              <CardContent>
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                  <Avatar src={p.photo_url ?? undefined} sx={{ width: 56, height: 56, bgcolor: 'secondary.main' }}>
                    {initials(p.name)}
                  </Avatar>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="h6" noWrap>
                      {p.name}
                    </Typography>
                    {p.relationship && (
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {p.relationship}
                      </Typography>
                    )}
                    <Typography variant="body2" color="text.secondary">
                      {p.story_count === 1 ? '1 story' : `${p.story_count} stories`}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>
    </Box>
  )
}
