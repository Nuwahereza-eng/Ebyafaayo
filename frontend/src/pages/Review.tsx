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
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useCallback, useEffect, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { api, audioUrl, formatDate, type Recording } from '../api'
import { usePoll } from '../hooks/usePoll'
import { SERIF } from '../theme'

export default function Review() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const [rec, setRec] = useState<Recording | null>(null)
  const [text, setText] = useState('')
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [savedNote, setSavedNote] = useState('')

  const load = useCallback(() => {
    api
      .recording(id)
      .then((r) => {
        setRec(r)
        if (!dirty) setText(r.transcript)
      })
      .catch((e) => setError(e.message))
  }, [id, dirty])

  useEffect(() => {
    load()
  }, [id]) // only on first load; polling handles updates
  const working = rec?.status === 'queued' || rec?.status === 'transcribing'
  usePoll(load, working)

  async function saveTranscript() {
    setBusy(true)
    setError('')
    try {
      const r = await api.saveTranscript(id, text)
      setRec((old) => (old ? { ...old, ...r } : old))
      setDirty(false)
      setSavedNote('Transcript saved.')
      return true
    } catch (e) {
      setError((e as Error).message)
      return false
    } finally {
      setBusy(false)
    }
  }

  async function createMemory() {
    if (!(await saveTranscript())) return
    setBusy(true)
    try {
      const m = await api.structure(id)
      navigate(`/memories/${m.id}`)
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  if (!rec) return error ? <Alert severity="error">{error}</Alert> : <LinearProgress />

  const minutes = Math.max(1, Math.round(rec.duration_s / 60))
  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" component="h1">
          Check the transcript
        </Typography>
        <Typography color="text.secondary">
          {rec.speaker_name} · recorded {formatDate(rec.created_at)} · consent recorded by {rec.consent_recorded_by}
        </Typography>
      </Box>

      <Card sx={{ position: { md: 'sticky' }, top: { md: 72 }, zIndex: 2 }}>
        <CardContent>
          <audio controls src={audioUrl(rec.id)} style={{ width: '100%' }} preload="metadata" />
        </CardContent>
      </Card>

      {working && (
        <Alert severity="info" icon={<CircularProgress size={20} />}>
          <Typography gutterBottom>
            {rec.status === 'queued' ? 'Waiting to start…' : 'Listening and writing down the story…'} This runs on
            this laptop, so a {minutes}-minute story can take several minutes. You can leave this page and come back.
          </Typography>
          <LinearProgress variant="determinate" value={rec.progress * 100} sx={{ mt: 1 }} />
        </Alert>
      )}
      {rec.status === 'failed' && (
        <Alert
          severity="warning"
          action={
            <Button color="inherit" startIcon={<Replay />} onClick={() => api.retryTranscription(id).then(setRec).catch((e) => setError(e.message))}>
              Try again
            </Button>
          }
        >
          Transcription did not finish: {rec.error} You can also type the story below while listening.
        </Alert>
      )}
      {rec.status === 'uploaded' && (
        <Alert severity="info">
          The Luganda speech model is not installed on this computer yet. Listen to the recording and type what the
          elder says below.
        </Alert>
      )}

      {!working && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              The elder's words
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Speech recognition makes mistakes, especially with names and places. Please listen and correct anything
              that is wrong. Gemma will only use what is written here.
            </Typography>
            <TextField
              multiline
              minRows={8}
              fullWidth
              value={text}
              onChange={(e) => {
                setText(e.target.value)
                setDirty(true)
                setSavedNote('')
              }}
              placeholder="Type or correct the story here…"
              slotProps={{ input: { sx: { fontFamily: SERIF, fontSize: '1.1rem', lineHeight: 1.7 } } }}
            />
            {rec.transcript_raw && rec.transcript_raw !== text && (
              <Accordion disableGutters elevation={0} sx={{ mt: 2, bgcolor: 'background.default' }}>
                <AccordionSummary>
                  <Typography variant="body2">What the speech model heard (before your corrections)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography sx={{ fontFamily: SERIF, whiteSpace: 'pre-wrap' }} color="text.secondary">
                    {rec.transcript_raw}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            )}
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
            {savedNote && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {savedNote}
              </Alert>
            )}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 2 }}>
              <Button variant="outlined" onClick={saveTranscript} disabled={busy || !dirty}>
                Save transcript
              </Button>
              <Button
                variant="contained"
                color="secondary"
                startIcon={busy ? <CircularProgress size={18} color="inherit" /> : <AutoAwesome />}
                onClick={createMemory}
                disabled={busy || !text.trim()}
              >
                Turn into a family memory with Gemma
              </Button>
              {rec.memory_id && (
                <Button component={RouterLink} to={`/memories/${rec.memory_id}`}>
                  Open the last memory
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Stack>
  )
}
