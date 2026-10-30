import AddPhotoAlternate from '@mui/icons-material/AddPhotoAlternateOutlined'
import DeleteOutline from '@mui/icons-material/DeleteOutlineOutlined'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Grid,
  IconButton,
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useState } from 'react'
import { api, type FamilyPhoto } from '../api'
import { usePoll } from '../hooks/usePoll'
import { SERIF } from '../theme'

function PhotoCard({ photo: initial, onChanged }: { photo: FamilyPhoto; onChanged: () => void }) {
  const [photo, setPhoto] = useState(initial)
  const [caption, setCaption] = useState(initial.caption)
  const [description, setDescription] = useState(initial.description)
  const [error, setError] = useState('')
  const dirty = caption !== photo.caption || description !== photo.description

  usePoll(() => {
    api.familyPhoto(photo.id).then((p) => {
      setPhoto(p)
      setDescription(p.description)
    })
  }, photo.status === 'describing')

  const save = () =>
    api.updateFamilyPhoto(photo.id, { caption, description, questions: photo.questions })
      .then(setPhoto)
      .catch((e) => setError(e.message))

  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardMedia component="img" image={photo.url} alt={caption || 'Family photo'} sx={{ maxHeight: 320, objectFit: 'contain', bgcolor: '#EFE7DC' }} />
      <CardContent>
        <Stack spacing={2}>
          <TextField
            label="Who is in this photo? Where, when? (written by the family)"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            multiline
            fullWidth
          />

          {photo.status === 'describing' && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Gemma is looking at the photo…
              </Typography>
              <LinearProgress />
            </Box>
          )}
          {photo.status === 'failed' && (
            <Alert severity="warning" action={
              <Button color="inherit" size="small" onClick={() => api.describeFamilyPhoto(photo.id).then(setPhoto).catch((e) => setError(e.message))}>
                Try again
              </Button>
            }>
              {photo.error || 'Gemma could not describe this photo.'}
            </Alert>
          )}
          {photo.status === 'ready' && (
            <>
              <TextField
                label="What Gemma can see"
                helperText="Gemma only describes what is in the picture. It never says who anyone is."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                multiline
                fullWidth
              />
              {photo.notes.map((n, i) => (
                <Alert key={i} severity="info">{n}</Alert>
              ))}
              {photo.questions.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Ask about this photo</Typography>
                  {photo.questions.map((q, i) => (
                    <Box key={i} sx={{ mb: 1 }}>
                      <Typography sx={{ fontFamily: SERIF }}>{q.luganda}</Typography>
                      <Typography variant="body2" color="text.secondary">{q.english}</Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </>
          )}
          {error && <Alert severity="error">{error}</Alert>}

          <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
            <IconButton aria-label="Delete photo" onClick={() => {
              if (confirm('Delete this photo from the app?')) api.deleteFamilyPhoto(photo.id).then(onChanged)
            }}>
              <DeleteOutline />
            </IconButton>
            <Button variant="contained" disabled={!dirty || photo.status === 'describing'} onClick={save}>Save</Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}

/** Old family photos on an elder's page. */
export default function FamilyPhotos({ personId, photos, onChanged }: { personId: number; photos: FamilyPhoto[]; onChanged: () => void }) {
  const [error, setError] = useState('')
  return (
    <Card>
      <CardContent>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, mb: 2 }}>
          <Box>
            <Typography variant="h5" component="h2">Old photos</Typography>
            <Typography variant="body2" color="text.secondary">
              Add a photo from the family album. Gemma describes what it can see and suggests questions to ask; you say who is in it.
            </Typography>
          </Box>
          <Button variant="outlined" component="label" startIcon={<AddPhotoAlternate />} sx={{ flexShrink: 0 }}>
            Add a photo
            <input hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => {
              const f = e.target.files?.[0]
              e.target.value = ''
              if (f) api.addFamilyPhoto(personId, f).then(onChanged).catch((err) => setError(err.message))
            }} />
          </Button>
        </Stack>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {photos.length === 0 && <Typography color="text.secondary">No photos yet.</Typography>}
        <Grid container spacing={2}>
          {photos.map((p) => (
            <Grid key={p.id} size={{ xs: 12, md: 6 }}>
              <PhotoCard photo={p} onChanged={onChanged} />
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  )
}
