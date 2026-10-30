import Print from '@mui/icons-material/Print'
import { Alert, Box, Button, Divider, LinearProgress, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, formatDate, type Person, type Remembrance } from '../api'
import { SERIF } from '../theme'

const ALL = 'all'

function Chapter({ r, first }: { r: Remembrance; first: boolean }) {
  const { person } = r
  return (
    <Box className={first ? undefined : 'page-break'} sx={{ mb: 6 }}>
      <Box sx={{ textAlign: 'center', py: 6 }}>
        {person.photo_url && (
          <Box component="img" src={person.photo_url} alt={person.name}
            sx={{ width: 180, height: 180, objectFit: 'cover', borderRadius: '50%', mb: 2 }} />
        )}
        <Typography variant="h3" component="h2">{person.name}</Typography>
        <Typography color="text.secondary" sx={{ fontFamily: SERIF }}>
          {[person.relationship, person.years].filter(Boolean).join(' · ')}
        </Typography>
        {person.about && <Typography sx={{ fontFamily: SERIF, mt: 2, maxWidth: 520, mx: 'auto' }}>{person.about}</Typography>}
      </Box>

      {r.memories.length === 0 && <Typography color="text.secondary" sx={{ textAlign: 'center' }}>No saved stories yet.</Typography>}
      {r.memories.map((m) => (
        <Box key={m.id} sx={{ mb: 5 }}>
          <Typography variant="h4" component="h3" className="avoid-break">{m.title}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Told by {m.speaker_name} on {formatDate(m.recorded_at)}. Recorded with their consent.
          </Typography>
          <Typography sx={{ fontFamily: SERIF, fontSize: '1.1rem', lineHeight: 1.8, whiteSpace: 'pre-wrap', mb: 2 }}>
            {m.data.luganda_text}
          </Typography>
          <Typography sx={{ fontFamily: SERIF, fontSize: '1.05rem', lineHeight: 1.8, whiteSpace: 'pre-wrap', fontStyle: 'italic', color: 'text.secondary' }}>
            {m.data.english_text}
          </Typography>
          {m.data.proverbs.length > 0 && (
            <Box sx={{ borderLeft: 3, borderColor: 'secondary.main', pl: 2, mt: 2 }} className="avoid-break">
              {m.data.proverbs.map((p, i) => (
                <Typography key={i} sx={{ fontFamily: SERIF }}>“{p.luganda}”: {p.english}</Typography>
              ))}
            </Box>
          )}
          {(m.data.clan || m.data.totem) && (
            <Typography variant="body2" sx={{ mt: 2 }}>
              {m.data.clan && <>Ekika (clan): <b>{m.data.clan.value}</b>. </>}
              {m.data.totem && <>Omuziro (totem): <b>{m.data.totem.value}</b>.</>}
            </Typography>
          )}
        </Box>
      ))}

      {r.photos.filter((p) => p.status === 'ready' || p.caption).length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h5" component="h3" gutterBottom>Photos</Typography>
          {r.photos.filter((p) => p.status === 'ready' || p.caption).map((p) => (
            <Box key={p.id} className="avoid-break" sx={{ mb: 3, textAlign: 'center' }}>
              <Box component="img" src={p.url} alt={p.caption || 'Family photo'} sx={{ maxWidth: '100%', maxHeight: 360 }} />
              {p.caption && <Typography sx={{ fontFamily: SERIF, mt: 1 }}>{p.caption}</Typography>}
              {p.description && (
                <Typography variant="body2" color="text.secondary" sx={{ fontFamily: SERIF, fontStyle: 'italic' }}>{p.description}</Typography>
              )}
            </Box>
          ))}
        </Box>
      )}

      {r.timeline.length > 0 && (
        <Box className="avoid-break" sx={{ mb: 4 }}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h5" component="h3" gutterBottom>Timeline</Typography>
          {r.timeline.map((t, i) => (
            <Typography key={i} sx={{ fontFamily: SERIF }}>
              <b>{t.year ?? '·'}</b> {t.description}
            </Typography>
          ))}
        </Box>
      )}
      {(r.people.length > 0 || r.places.length > 0) && (
        <Box className="avoid-break">
          <Typography variant="h5" component="h3" gutterBottom>People and places in these stories</Typography>
          <Typography sx={{ fontFamily: SERIF }}>
            {r.people.map((p) => (p.relationships?.length ? `${p.name} (${p.relationships.join(', ')})` : p.name)).join(' · ')}
          </Typography>
          <Typography sx={{ fontFamily: SERIF, mt: 1 }}>{r.places.map((p) => p.name).join(' · ')}</Typography>
        </Box>
      )}
    </Box>
  )
}

export default function Book() {
  const [params, setParams] = useSearchParams()
  const selected = params.get('person') ?? ALL
  const [people, setPeople] = useState<Person[]>([])
  const [book, setBook] = useState<Remembrance[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.people().then(setPeople).catch(() => {})
  }, [])
  useEffect(() => {
    setBook(null)
    api.book(selected === ALL ? undefined : Number(selected)).then(setBook).catch((e) => setError(e.message))
  }, [selected])

  return (
    <Box>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} className="no-print" sx={{ mb: 3, alignItems: { sm: 'center' } }}>
        <TextField select size="small" label="Book for" value={selected} sx={{ minWidth: 220 }}
          onChange={(e) => setParams(e.target.value === ALL ? {} : { person: e.target.value })}>
          <MenuItem value={ALL}>The whole family</MenuItem>
          {people.map((p) => <MenuItem key={p.id} value={String(p.id)}>{p.name}</MenuItem>)}
        </TextField>
        <Button variant="contained" startIcon={<Print />} onClick={() => window.print()} disabled={!book}>
          Save as PDF
        </Button>
        <Typography variant="body2" color="text.secondary">Choose “Save as PDF” in the print window.</Typography>
      </Stack>
      {error && <Alert severity="error">{error}</Alert>}
      {!book && !error && <LinearProgress />}
      {book && (
        <Box sx={{ bgcolor: 'background.paper', p: { xs: 2, sm: 6 }, borderRadius: 2, '@media print': { p: 0 } }}>
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <Typography variant="overline" color="text.secondary">Ebyafaayo</Typography>
            <Typography variant="h2" component="h1" sx={{ fontSize: { xs: '2.2rem', sm: '3.2rem' } }}>
              {selected === ALL ? 'Our family’s stories' : `The stories of ${book[0]?.person.name ?? ''}`}
            </Typography>
            <Typography color="text.secondary" sx={{ fontFamily: SERIF, mt: 1 }}>
              In their own words, {new Date().getFullYear()}
            </Typography>
          </Box>
          {book.map((r, i) => <Chapter key={r.person.id} r={r} first={i === 0} />)}
          <Typography variant="caption" color="text.secondary" component="p" sx={{ textAlign: 'center', mt: 6 }}>
            Transcribed with Sunbird AI's open Luganda speech model and written with Gemma 4, both running on our own
            computer, then checked and corrected by the family.
          </Typography>
        </Box>
      )}
    </Box>
  )
}
