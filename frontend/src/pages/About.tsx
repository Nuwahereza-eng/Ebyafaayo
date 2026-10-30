import CheckCircle from '@mui/icons-material/CheckCircle'
import ErrorOutline from '@mui/icons-material/ErrorOutlineOutlined'
import { Box, Card, CardContent, Link, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, type Status } from '../api'

function Ready({ ok, label }: { ok: boolean | undefined; label: string }) {
  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      {ok ? <CheckCircle color="secondary" fontSize="small" /> : <ErrorOutline color="warning" fontSize="small" />}
      <Typography>{label}: {ok ? 'ready on this computer' : 'not ready'}</Typography>
    </Stack>
  )
}

export default function About() {
  const [status, setStatus] = useState<Status | null>(null)
  useEffect(() => {
    api.status().then(setStatus).catch(() => {})
  }, [])

  return (
    <Stack spacing={3}>
      <Typography variant="h4" component="h1">About Ebyafaayo</Typography>
      <Typography sx={{ fontFamily: '"Lora", serif', fontSize: '1.1rem' }}>
        <i>Ebyafaayo</i> means history, the things that happened, in Luganda. This app helps a family record an elder
        telling a story, write it down, and keep it as a family memory.
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="h5" component="h2" gutterBottom>Private by design</Typography>
          <Box component="ul" sx={{ pl: 2.5, m: 0, '& li': { mb: 1 } }}>
            <li>Everything runs on this computer: the recordings, the speech model, Gemma and the database.</li>
            <li>No analytics, no telemetry, no cloud AI. After the models are downloaded, the app works with the internet switched off.</li>
            <li>Every recording is saved with the consent the family recorded.</li>
            <li>The AI only uses what the elder said. Names, clans (ekika), totems (omuziro), dates and relationships are never guessed, and every item links back to the sentence it came from.</li>
            <li>The family checks and can change everything before it is saved.</li>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h5" component="h2" gutterBottom>Open models</Typography>
          <Stack spacing={1} sx={{ mb: 2 }}>
            <Ready ok={status?.asr.ready} label="Sunbird speech model" />
            <Ready ok={status?.gemma.model_ready} label={`Gemma 4 (${status?.gemma.model ?? '…'}) through Ollama`} />
          </Stack>
          <Box component="ul" sx={{ pl: 2.5, m: 0, '& li': { mb: 1 } }}>
            <li>
              <b>Speech to text:</b>{' '}
              <Link href="https://huggingface.co/Sunbird/asr-whisper-large-v3-salt">Sunbird/asr-whisper-large-v3-salt</Link>{' '}
              by Sunbird AI (MIT licence), adapted from OpenAI Whisper large-v3 for Luganda and other Ugandan languages.
              It runs here through faster-whisper (CTranslate2, int8).
            </li>
            <li>
              <b>Writing, translation and extraction:</b> <Link href="https://ai.google.dev/gemma">Gemma 4</Link> by Google
              DeepMind (open weights, Gemma Terms of Use), run locally with <Link href="https://ollama.com">Ollama</Link>.
            </li>
            <li>Made with FastAPI, SQLite, React and Material UI. Fonts: Lora and Inter, stored with the app.</li>
          </Box>
        </CardContent>
      </Card>
    </Stack>
  )
}
