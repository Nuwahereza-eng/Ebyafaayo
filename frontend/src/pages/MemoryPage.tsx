import AutoAwesome from '@mui/icons-material/AutoAwesome'
import Replay from '@mui/icons-material/Replay'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  IconButton,
  LinearProgress,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import DeleteOutline from '@mui/icons-material/DeleteOutlineOutlined'
import { useCallback, useEffect, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { api, type Attribute, type Memory, type MemoryData } from '../api'
import ItemList from '../components/ItemList'
import Source from '../components/Source'
import { usePoll } from '../hooks/usePoll'
import { SERIF } from '../theme'

const CONFIDENCE = ['clear', 'unclear']

function Generating({ memory }: { memory: Memory }) {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    const started = Date.now()
    const t = setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <Card>
      <CardContent sx={{ textAlign: 'center', py: 5 }}>
        <AutoAwesome color="secondary" sx={{ fontSize: 40, mb: 1 }} />
        <Typography variant="h5" gutterBottom>
          Gemma is writing the memory…
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 480, mx: 'auto', mb: 3 }}>
          Gemma 4 runs on this laptop, without the internet. It is cleaning up the Luganda, translating it into English and
          noting the people, places and times the elder mentions. This can take a few minutes.
        </Typography>
        <LinearProgress color="secondary" sx={{ maxWidth: 360, mx: 'auto', mb: 1 }} />
        <Typography variant="body2" color="text.secondary">
          {memory.progress_chars > 0 ? `${memory.progress_chars} characters written` : 'Reading the story'} · {elapsed}s
        </Typography>
      </CardContent>
    </Card>
  )
}

function AttributeField({
  label,
  help,
  value,
  onChange,
}: {
  label: string
  help: string
  value: Attribute | null
  onChange: (v: Attribute | null) => void
}) {
  return (
    <Box sx={{ flex: 1 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        {label}
      </Typography>
      {value ? (
        <Box>
          <Stack direction="row" sx={{ alignItems: 'center' }}>
            <TextField size="small" value={value.value} onChange={(e) => onChange({ ...value, value: e.target.value, grounded: null })} fullWidth />
            <Source sentence={value.source_sentence} grounded={value.grounded} />
            <IconButton aria-label={`Remove ${label}`} onClick={() => onChange(null)}>
              <DeleteOutline fontSize="small" />
            </IconButton>
          </Stack>
          <TextField
            size="small"
            variant="standard"
            fullWidth
            label="Source sentence"
            value={value.source_sentence}
            onChange={(e) => onChange({ ...value, source_sentence: e.target.value, grounded: null })}
            slotProps={{ input: { sx: { fontFamily: SERIF, fontSize: '0.9rem', fontStyle: 'italic' } } }}
          />
        </Box>
      ) : (
        <Box>
          <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
            {help}
          </Typography>
          <Button size="small" onClick={() => onChange({ value: '', source_sentence: '', grounded: null })}>
            The elder said it, add it
          </Button>
        </Box>
      )}
    </Box>
  )
}

export default function MemoryPage() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const [memory, setMemory] = useState<Memory | null>(null)
  const [title, setTitle] = useState('')
  const [data, setData] = useState<MemoryData | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState('')

  const load = useCallback(() => {
    api
      .memory(id)
      .then((m) => {
        setMemory(m)
        if (m.status === 'draft' || m.status === 'saved') {
          setData((d) => d ?? m.data)
          setTitle((t) => t || m.title)
        }
      })
      .catch((e) => setError(e.message))
  }, [id])

  useEffect(() => {
    setData(null)
    setTitle('')
    load()
  }, [load])
  usePoll(load, memory?.status === 'generating')

  const set = <K extends keyof MemoryData>(key: K, value: MemoryData[K]) => setData((d) => (d ? { ...d, [key]: value } : d))

  async function save(final: boolean) {
    if (!data) return
    setBusy(true)
    setError('')
    try {
      const m = await api.updateMemory(id, title, data, final)
      setMemory(m)
      if (final) navigate(`/people/${m.person_id}`)
      else setToast('Draft saved')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function regenerate() {
    if (!memory) return
    try {
      const m = await api.structure(memory.recording_id)
      navigate(`/memories/${m.id}`)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (!memory) return error ? <Alert severity="error">{error}</Alert> : <LinearProgress />
  if (memory.status === 'generating') return <Generating memory={memory} />
  if (memory.status === 'failed')
    return (
      <Stack spacing={2}>
        <Alert severity="warning">Gemma could not finish this memory: {memory.error}</Alert>
        <Stack direction="row" spacing={2}>
          <Button variant="contained" startIcon={<Replay />} onClick={regenerate}>
            Try again
          </Button>
          <Button component={RouterLink} to={`/recordings/${memory.recording_id}`}>
            Back to the transcript
          </Button>
        </Stack>
        {error && <Alert severity="error">{error}</Alert>}
      </Stack>
    )
  if (!data) return <LinearProgress />

  const lowSimilarity = (data.luganda_similarity ?? 1) < 0.85

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" color="text.secondary">
          A story from {memory.person.name} · {memory.status === 'saved' ? 'saved' : 'draft, please check everything'}
        </Typography>
        <TextField
          fullWidth
          variant="standard"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          aria-label="Title"
          slotProps={{ input: { sx: { fontFamily: SERIF, fontSize: { xs: '1.6rem', sm: '2.1rem' }, fontWeight: 600 } } }}
        />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Written by {memory.model} on this laptop in {Math.round(memory.generation_seconds)} seconds. Gemma only used the
          transcript. Hover over or tap <Source sentence="The sentence each item came from appears here." /> to see where each item came from.
        </Typography>
      </Box>

      {(data.notes ?? []).map((n) => (
        <Alert severity="warning" key={n}>
          {n}
        </Alert>
      ))}
      {lowSimilarity && (
        <Alert severity="warning">
          Gemma's Luganda version differs from your transcript by more than small fixes. Please compare them and keep the
          elder's own words.
        </Alert>
      )}

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" component="h2" gutterBottom>
                Mu Luganda
              </Typography>
              <TextField
                multiline
                fullWidth
                minRows={6}
                value={data.luganda_text}
                onChange={(e) => set('luganda_text', e.target.value)}
                slotProps={{ input: { sx: { fontFamily: SERIF, fontSize: '1.05rem', lineHeight: 1.7 } } }}
              />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" component="h2" gutterBottom>
                In English
              </Typography>
              <TextField
                multiline
                fullWidth
                minRows={6}
                value={data.english_text}
                onChange={(e) => set('english_text', e.target.value)}
                slotProps={{ input: { sx: { fontFamily: SERIF, fontSize: '1.05rem', lineHeight: 1.7 } } }}
              />
              <Typography variant="caption" color="text.secondary">
                Machine translation. Please check it with someone who speaks both languages.
              </Typography>
            </Box>
          </Stack>

          <Accordion disableGutters elevation={0} sx={{ mt: 2, bgcolor: 'background.default' }}>
            <AccordionSummary>
              <Typography variant="body2">
                The transcript Gemma used, and {data.changes_made.length} change{data.changes_made.length === 1 ? '' : 's'} it made
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography sx={{ fontFamily: SERIF, whiteSpace: 'pre-wrap', mb: 2 }} color="text.secondary">
                {memory.transcript}
              </Typography>
              <ItemList
                title="Changes Gemma made to the Luganda"
                items={data.changes_made}
                sourced={false}
                fields={[
                  { key: 'original', label: 'Original', serif: true },
                  { key: 'corrected', label: 'Corrected', serif: true },
                  { key: 'reason', label: 'Why' },
                ]}
                empty={{ original: '', corrected: '', reason: '' }}
                emptyText="No changes."
                onChange={(v) => set('changes_made', v)}
              />
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack spacing={3} divider={<Divider />}>
            <ItemList
              title="People mentioned"
              help="Relationships are only filled in when the elder says them."
              items={data.people}
              fields={[
                { key: 'name', label: 'Name' },
                { key: 'relationship_to_speaker', label: 'Relationship to speaker' },
                { key: 'confidence', label: 'Confidence', options: CONFIDENCE, flex: 0 },
              ]}
              empty={{ name: '', relationship_to_speaker: null, source_sentence: '', confidence: 'clear', grounded: null }}
              emptyText="No people named."
              onChange={(v) => set('people', v)}
            />
            <ItemList
              title="Places"
              items={data.places}
              fields={[
                { key: 'name', label: 'Place' },
                { key: 'confidence', label: 'Confidence', options: CONFIDENCE, flex: 0 },
              ]}
              empty={{ name: '', source_sentence: '', confidence: 'clear', grounded: null }}
              emptyText="No places named."
              onChange={(v) => set('places', v)}
            />
            <ItemList
              title="Times"
              help="Years and periods the elder mentions. These make the timeline."
              items={data.time_periods}
              fields={[
                { key: 'description', label: 'When' },
                { key: 'confidence', label: 'Confidence', options: CONFIDENCE, flex: 0 },
              ]}
              empty={{ description: '', source_sentence: '', confidence: 'clear', grounded: null }}
              emptyText="No times mentioned."
              onChange={(v) => set('time_periods', v)}
            />
            <Box>
              <Typography variant="h6" component="h3" gutterBottom>
                Clan and totem
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3}>
                <AttributeField
                  label="Ekika (clan)"
                  help="Not mentioned in this story. We never guess a clan."
                  value={data.clan}
                  onChange={(v) => set('clan', v)}
                />
                <AttributeField
                  label="Omuziro (totem)"
                  help="Not mentioned in this story. We never guess a totem."
                  value={data.totem}
                  onChange={(v) => set('totem', v)}
                />
              </Stack>
            </Box>
            <ItemList
              title="Engero (proverbs)"
              items={data.proverbs}
              fields={[
                { key: 'luganda', label: 'Luganda', serif: true, flex: 2 },
                { key: 'english', label: 'English', serif: true, flex: 2 },
              ]}
              empty={{ luganda: '', english: '', source_sentence: '', grounded: null }}
              emptyText="No proverbs in this story."
              onChange={(v) => set('proverbs', v)}
            />
            <ItemList
              title="Questions to ask next time"
              help="Gentle questions about things the elder mentioned but did not explain. Gemma's Luganda can be awkward, so please fix the wording before you ask."
              items={data.follow_up_questions}
              sourced={false}
              fields={[
                { key: 'luganda', label: 'Luganda', serif: true, multiline: true },
                { key: 'english', label: 'English', serif: true, multiline: true },
              ]}
              empty={{ luganda: '', english: '', answered: false }}
              emptyText="No questions."
              onChange={(v) => set('follow_up_questions', v)}
            />
          </Stack>
        </CardContent>
      </Card>

      {error && <Alert severity="error">{error}</Alert>}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ position: 'sticky', bottom: 16 }}>
        <Button variant="contained" color="secondary" size="large" onClick={() => save(true)} disabled={busy}
          startIcon={busy ? <CircularProgress size={18} color="inherit" /> : undefined}>
          Save to {memory.person.name}'s remembrance page
        </Button>
        <Button variant="outlined" onClick={() => save(false)} disabled={busy} sx={{ bgcolor: 'background.paper' }}>
          Save draft
        </Button>
        <Button onClick={regenerate} disabled={busy} sx={{ bgcolor: 'background.paper' }}>
          Ask Gemma again
        </Button>
      </Stack>
      <Snackbar open={!!toast} autoHideDuration={2500} onClose={() => setToast('')} message={toast} />
    </Stack>
  )
}
