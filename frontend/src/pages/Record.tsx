import FiberManualRecord from '@mui/icons-material/FiberManualRecord'
import LockOutlined from '@mui/icons-material/LockOutlined'
import Stop from '@mui/icons-material/Stop'
import UploadFile from '@mui/icons-material/UploadFile'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api, type Person, type Status } from '../api'

const NEW = 'new'

function pickMimeType() {
  for (const t of ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(t)) return t
  }
  return ''
}

function formatTime(s: number) {
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}

export default function Record() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [people, setPeople] = useState<Person[]>([])
  const [status, setStatus] = useState<Status | null>(null)

  // Consent
  const [personId, setPersonId] = useState<string>(params.get('person') ?? NEW)
  const [newName, setNewName] = useState('')
  const [newRelationship, setNewRelationship] = useState('')
  const [speaker, setSpeaker] = useState('')
  const [language, setLanguage] = useState('lug')
  const [recordedBy, setRecordedBy] = useState('')
  const [consent, setConsent] = useState(false)

  // Audio
  const [recording, setRecording] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [audio, setAudio] = useState<Blob | null>(null)
  const [audioName, setAudioName] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const recorder = useRef<MediaRecorder | null>(null)
  const audioUrl = useMemo(() => (audio ? URL.createObjectURL(audio) : ''), [audio])
  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => {
    api.people().then(setPeople).catch(() => {})
    api.status().then(setStatus).catch(() => {})
    return () => {
      clearInterval(timer.current)
      recorder.current?.stream.getTracks().forEach((t) => t.stop())
    }
  }, [])

  const person = people.find((p) => String(p.id) === personId)
  useEffect(() => {
    if (person && !speaker) setSpeaker(person.name)
  }, [person, speaker])

  const elderName = personId === NEW ? newName : person?.name ?? ''
  const speakerName = speaker || elderName
  const consentText = (status?.consent_text ?? '{speaker} agrees to be recorded telling this story.').replace(
    '{speaker}',
    speakerName || 'The speaker',
  )
  const consentReady = !!elderName.trim() && !!speakerName.trim() && !!recordedBy.trim() && consent

  async function startRecording() {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = pickMimeType()
      const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      const parts: BlobPart[] = []
      rec.ondataavailable = (e) => e.data.size && parts.push(e.data)
      rec.onstop = () => {
        const type = rec.mimeType || 'audio/webm'
        setAudio(new Blob(parts, { type }))
        setAudioName(`recording.${type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'}`)
        stream.getTracks().forEach((t) => t.stop())
      }
      rec.start(1000)
      recorder.current = rec
      setSeconds(0)
      setRecording(true)
      const started = Date.now()
      timer.current = window.setInterval(() => setSeconds((Date.now() - started) / 1000), 250)
    } catch {
      setError('Could not use the microphone. Allow microphone access in the browser, or upload a file instead.')
    }
  }

  function stopRecording() {
    recorder.current?.stop()
    clearInterval(timer.current)
    setRecording(false)
  }

  async function save() {
    if (!audio) return
    setSaving(true)
    setError('')
    const f = new FormData()
    f.append('audio', audio, audioName)
    if (personId === NEW) {
      f.append('new_person_name', newName)
      f.append('new_person_relationship', newRelationship)
    } else f.append('person_id', personId)
    f.append('speaker_name', speakerName)
    f.append('language', language)
    f.append('consent_given', String(consent))
    f.append('consent_recorded_by', recordedBy)
    try {
      const rec = await api.createRecording(f)
      navigate(`/recordings/${rec.id}`)
    } catch (e) {
      setError((e as Error).message)
      setSaving(false)
    }
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4" component="h1">
        Record a story
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            1. Who is telling the story?
          </Typography>
          <Stack spacing={2}>
            <TextField select label="Whose story is this?" value={personId} onChange={(e) => setPersonId(e.target.value)}>
              {people.map((p) => (
                <MenuItem key={p.id} value={String(p.id)}>
                  {p.name}
                  {p.relationship ? ` · ${p.relationship}` : ''}
                </MenuItem>
              ))}
              <MenuItem value={NEW}>+ Add a new elder</MenuItem>
            </TextField>
            {personId === NEW && (
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField label="Elder's name" value={newName} onChange={(e) => setNewName(e.target.value)} fullWidth required />
                <TextField
                  label="Who are they to the family?"
                  placeholder="e.g. Jjajja (grandmother)"
                  value={newRelationship}
                  onChange={(e) => setNewRelationship(e.target.value)}
                  fullWidth
                />
              </Stack>
            )}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Speaker's name"
                helperText="Usually the elder, unless someone tells the story about them"
                value={speaker}
                placeholder={elderName}
                onChange={(e) => setSpeaker(e.target.value)}
                fullWidth
              />
              <TextField select label="Language" value={language} onChange={(e) => setLanguage(e.target.value)} fullWidth>
                {Object.entries(status?.languages ?? { lug: 'Luganda' }).map(([code, name]) => (
                  <MenuItem key={code} value={code}>
                    {name}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ borderColor: consent ? 'secondary.main' : undefined }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            2. Ask for consent first
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            Read this to the speaker in a language they understand, and only continue if they agree.
          </Typography>
          <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 2, fontFamily: '"Lora", serif', mb: 2 }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
              <LockOutlined fontSize="small" sx={{ mt: 0.3, color: 'secondary.main' }} />
              <span>{consentText}</span>
            </Stack>
          </Box>
          <Stack spacing={2}>
            <TextField
              label="Your name (the family member asking)"
              value={recordedBy}
              onChange={(e) => setRecordedBy(e.target.value)}
              required
            />
            <FormControlLabel
              control={<Checkbox checked={consent} onChange={(e) => setConsent(e.target.checked)} color="secondary" />}
              label={`${speakerName || 'The speaker'} has agreed to be recorded.`}
            />
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ opacity: consentReady ? 1 : 0.55 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            3. Record or upload
          </Typography>
          {!consentReady && (
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Fill in the names and tick the consent box to start.
            </Typography>
          )}
          <Stack spacing={2} sx={{ alignItems: 'center', py: 2 }}>
            <Button
              variant="contained"
              color={recording ? 'error' : 'primary'}
              disabled={!consentReady || saving}
              onClick={recording ? stopRecording : startRecording}
              aria-label={recording ? 'Stop recording' : 'Start recording'}
              sx={{ width: 120, height: 120, borderRadius: '50%', flexDirection: 'column' }}
            >
              {recording ? <Stop sx={{ fontSize: 48 }} /> : <FiberManualRecord sx={{ fontSize: 48 }} />}
              {recording ? 'Stop' : 'Record'}
            </Button>
            <Typography variant="h5" sx={{ fontVariantNumeric: 'tabular-nums' }} aria-live="polite">
              {formatTime(seconds)}
            </Typography>
            <Divider flexItem>or</Divider>
            <Button variant="outlined" component="label" startIcon={<UploadFile />} disabled={!consentReady || recording || saving}>
              Upload an audio file
              <input
                hidden
                type="file"
                accept="audio/*,video/mp4,.m4a,.mp3,.wav,.ogg,.webm,.aac,.amr"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    setAudio(file)
                    setAudioName(file.name)
                    setSeconds(0)
                  }
                }}
              />
            </Button>
            {audio && !recording && (
              <Box sx={{ width: '100%' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Listen back before saving: {audioName}
                </Typography>
                <audio controls src={audioUrl} style={{ width: '100%' }} />
              </Box>
            )}
          </Stack>
          {error && <Alert severity="error">{error}</Alert>}
          <Button
            variant="contained"
            color="secondary"
            size="large"
            fullWidth
            disabled={!consentReady || !audio || recording || saving}
            onClick={save}
            startIcon={saving ? <CircularProgress size={18} color="inherit" /> : undefined}
            sx={{ mt: 2 }}
          >
            {saving ? 'Saving…' : 'Save and transcribe'}
          </Button>
        </CardContent>
      </Card>
    </Stack>
  )
}
