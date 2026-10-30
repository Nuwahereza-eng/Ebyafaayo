import Edit from '@mui/icons-material/Edit'
import MenuBook from '@mui/icons-material/MenuBook'
import Mic from '@mui/icons-material/Mic'
import PhotoCamera from '@mui/icons-material/PhotoCamera'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import { useCallback, useEffect, useState } from 'react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { api, formatDate, type Draft, type MentionSummary, type Remembrance as R } from '../api'
import Source from '../components/Source'
import { SERIF } from '../theme'
import { initials } from './Home'

function Mentions({ items, empty }: { items: MentionSummary[]; empty: string }) {
  if (!items.length) return <Typography color="text.secondary">{empty}</Typography>
  return (
    <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1 }}>
      {items.map((m) => (
        <Tooltip
          key={m.name}
          enterTouchDelay={0}
          arrow
          title={
            <Box>
              {m.relationships?.length ? <b>{m.relationships.join(', ')}</b> : null}
              {m.stories.map((s, i) => (
                <Box key={i} sx={{ mt: 0.5 }}>
                  “{s.source_sentence}” <i>({s.title})</i>
                </Box>
              ))}
            </Box>
          }
        >
          <Chip label={m.relationships?.length ? `${m.name} · ${m.relationships[0]}` : m.name} variant="outlined" />
        </Tooltip>
      ))}
    </Stack>
  )
}

function EditPerson({ data, onClose, onSaved }: { data: R['person']; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: data.name, relationship: data.relationship, years: data.years, about: data.about })
  const field = (key: keyof typeof form, label: string, multiline = false) => (
    <TextField label={label} value={form[key]} multiline={multiline} minRows={multiline ? 3 : undefined}
      onChange={(e) => setForm({ ...form, [key]: e.target.value })} fullWidth />
  )
  return (
    <Dialog open onClose={onClose} fullWidth>
      <DialogTitle>About {data.name}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {field('name', 'Name')}
          {field('relationship', 'Who they are to the family')}
          {field('years', 'Years (e.g. 1938 – 2019)')}
          {field('about', 'A few words about them', true)}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={() => api.updatePerson(data.id, form).then(onSaved)}>Save</Button>
      </DialogActions>
    </Dialog>
  )
}

export default function Remembrance() {
  const id = Number(useParams().id)
  const [page, setPage] = useState<R | null>(null)
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    api.remembrance(id).then(setPage).catch((e) => setError(e.message))
    api.drafts(id).then(setDrafts).catch(() => {})
  }, [id])
  useEffect(load, [load])

  if (!page) return error ? <Alert severity="error">{error}</Alert> : <LinearProgress />
  const { person } = page

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ alignItems: 'center' }}>
        <Box sx={{ position: 'relative' }}>
          <Avatar src={person.photo_url ?? undefined} sx={{ width: 120, height: 120, fontSize: 40, bgcolor: 'secondary.main' }}>
            {initials(person.name)}
          </Avatar>
          <IconButton component="label" aria-label="Add a photo" size="small"
            sx={{ position: 'absolute', bottom: 0, right: 0, bgcolor: 'background.paper', boxShadow: 1, '&:hover': { bgcolor: 'background.paper' } }}>
            <PhotoCamera fontSize="small" />
            <input hidden type="file" accept="image/*" onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) api.uploadPhoto(person.id, f).then(load).catch((err) => setError(err.message))
            }} />
          </IconButton>
        </Box>
        <Box sx={{ flex: 1, textAlign: { xs: 'center', sm: 'left' } }}>
          <Typography variant="h3" component="h1" sx={{ fontSize: { xs: '2rem', sm: '2.6rem' } }}>
            {person.name}
            <IconButton aria-label="Edit details" onClick={() => setEditing(true)} sx={{ ml: 1 }}>
              <Edit />
            </IconButton>
          </Typography>
          <Typography color="text.secondary">{[person.relationship, person.years].filter(Boolean).join(' · ')}</Typography>
          {person.about && <Typography sx={{ fontFamily: SERIF, mt: 1 }}>{person.about}</Typography>}
        </Box>
      </Stack>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <Button variant="contained" startIcon={<Mic />} component={RouterLink} to={`/record?person=${person.id}`}>
          Record another story
        </Button>
        <Button variant="outlined" startIcon={<MenuBook />} component={RouterLink} to={`/book?person=${person.id}`}>
          Memory book
        </Button>
      </Stack>

      {drafts.length > 0 && (
        <Alert severity="info">
          <Typography gutterBottom>Stories still being prepared:</Typography>
          {drafts.map((d) => (
            <Box key={d.recording_id}>
              <RouterLink to={d.memory_id ? `/memories/${d.memory_id}` : `/recordings/${d.recording_id}`}>
                {formatDate(d.created_at)}: {d.preview ? `“${d.preview}…”` : d.status}
              </RouterLink>
            </Box>
          ))}
        </Alert>
      )}

      <Box>
        <Typography variant="h5" component="h2" gutterBottom>
          Stories
        </Typography>
        {page.memories.length === 0 && <Typography color="text.secondary">No saved stories yet.</Typography>}
        {page.memories.map((m, i) => (
          <Accordion key={m.id} defaultExpanded={i === 0} disableGutters variant="outlined" sx={{ mb: 1 }}>
            <AccordionSummary>
              <Box>
                <Typography variant="h6">{m.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Told by {m.speaker_name} · {formatDate(m.recorded_at)}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
                <Typography sx={{ flex: 1, fontFamily: SERIF, whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{m.data.luganda_text}</Typography>
                <Typography sx={{ flex: 1, fontFamily: SERIF, whiteSpace: 'pre-wrap', lineHeight: 1.8, color: 'text.secondary' }}>
                  {m.data.english_text}
                </Typography>
              </Stack>
              {m.data.proverbs.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  {m.data.proverbs.map((p, j) => (
                    <Typography key={j} sx={{ fontFamily: SERIF, fontStyle: 'italic' }}>
                      “{p.luganda}” ({p.english}) <Source sentence={p.source_sentence} grounded={p.grounded} />
                    </Typography>
                  ))}
                </Box>
              )}
              <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                <audio controls preload="none" src={`/api/recordings/${m.recording_id}/audio`} style={{ maxWidth: '100%' }} />
                <Button component={RouterLink} to={`/memories/${m.id}`}>Edit</Button>
              </Stack>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>

      <Card>
        <CardContent>
          <Typography variant="h5" component="h2" gutterBottom>
            Timeline
          </Typography>
          {page.timeline.length === 0 && <Typography color="text.secondary">No times mentioned yet.</Typography>}
          <Box component="ol" sx={{ listStyle: 'none', p: 0, m: 0, borderLeft: 3, borderColor: 'secondary.main', pl: 2 }}>
            {page.timeline.map((t, i) => (
              <Box component="li" key={i} sx={{ mb: 2, position: 'relative' }}>
                <Box sx={{ position: 'absolute', left: -25, top: 6, width: 12, height: 12, borderRadius: '50%', bgcolor: 'secondary.main' }} />
                <Typography sx={{ fontWeight: 600 }}>
                  {t.year ?? 'Undated'} · {t.description}
                  <Source sentence={t.source_sentence} />
                </Typography>
                <Typography variant="body2" color="text.secondary">from “{t.title}”</Typography>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h5" component="h2" gutterBottom>People they spoke of</Typography>
          <Mentions items={page.people} empty="No one named yet." />
          <Typography variant="h5" component="h2" sx={{ mt: 3 }} gutterBottom>Places</Typography>
          <Mentions items={page.places} empty="No places named yet." />
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h5" component="h2">Questions to ask {person.name} next time</Typography>
          <Typography variant="body2" color="text.secondary">Tick a question when it has been answered (and record the answer as a new story).</Typography>
          {page.open_questions.length === 0 && <Typography color="text.secondary" sx={{ mt: 1 }}>No open questions.</Typography>}
          <List>
            {page.open_questions.map((q) => (
              <ListItem key={`${q.memory_id}-${q.index}`} disablePadding>
                <ListItemButton onClick={() => api.markQuestion(q.memory_id, q.index, true).then(load)}>
                  <ListItemIcon><Checkbox edge="start" tabIndex={-1} /></ListItemIcon>
                  <ListItemText
                    primary={<span style={{ fontFamily: SERIF }}>{q.luganda}</span>}
                    secondary={`${q.english} (from “${q.title}”)`}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
      {editing && <EditPerson data={person} onClose={() => setEditing(false)} onSaved={() => { setEditing(false); load() }} />}
    </Stack>
  )
}
