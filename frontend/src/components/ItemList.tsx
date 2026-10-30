import Add from '@mui/icons-material/Add'
import DeleteOutline from '@mui/icons-material/DeleteOutlineOutlined'
import { Box, Button, Chip, IconButton, MenuItem, Stack, TextField, Typography } from '@mui/material'
import Source from './Source'

export interface FieldDef<T> {
  key: keyof T & string
  label: string
  serif?: boolean
  multiline?: boolean
  options?: string[]
  flex?: number
}

interface Props<T> {
  title: string
  help?: string
  items: T[]
  fields: FieldDef<T>[]
  empty: T
  emptyText: string
  onChange: (items: T[]) => void
  sourced?: boolean
}

/** An editable list of extracted items, each linked to its source sentence. */
export default function ItemList<T extends object>({ title, help, items, fields, empty, emptyText, onChange, sourced = true }: Props<T>) {
  // Once the family edits an item, it counts as checked by them, so the "not found" warning goes away.
  const update = (i: number, key: keyof T, value: unknown) =>
    onChange(
      items.map((it, j) =>
        j === i
          ? { ...it, [key]: value === '' && key === 'relationship_to_speaker' ? null : value, ...(sourced ? { grounded: null } : {}) }
          : it,
      ),
    )

  return (
    <Box>
      <Typography variant="h6" component="h3">
        {title}
      </Typography>
      {help && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {help}
        </Typography>
      )}
      {items.length === 0 && (
        <Typography color="text.secondary" sx={{ fontStyle: 'italic', mb: 1 }}>
          {emptyText}
        </Typography>
      )}
      <Stack spacing={1.5}>
        {items.map((item, i) => {
          const rec = item as Record<string, unknown>
          return (
            <Box
              key={i}
              sx={{
                p: 1.5,
                borderRadius: 2,
                border: 1,
                borderColor: rec.grounded === false ? 'warning.light' : 'divider',
                bgcolor: rec.grounded === false ? '#FFF8E1' : 'background.paper',
              }}
            >
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ alignItems: { sm: 'center' } }}>
                {fields.map((f) =>
                  f.options ? (
                    <TextField
                      key={f.key}
                      select
                      size="small"
                      label={f.label}
                      value={(rec[f.key] as string) ?? ''}
                      onChange={(e) => update(i, f.key, e.target.value)}
                      sx={{ minWidth: 110 }}
                    >
                      {f.options.map((o) => (
                        <MenuItem key={o} value={o}>
                          {o}
                        </MenuItem>
                      ))}
                    </TextField>
                  ) : (
                    <TextField
                      key={f.key}
                      size="small"
                      label={f.label}
                      value={(rec[f.key] as string) ?? ''}
                      onChange={(e) => update(i, f.key, e.target.value)}
                      multiline={f.multiline}
                      sx={{ flex: f.flex ?? 1 }}
                      slotProps={f.serif ? { input: { sx: { fontFamily: '"Lora", serif' } } } : undefined}
                    />
                  ),
                )}
                <Stack direction="row" sx={{ alignItems: 'center', flexShrink: 0 }}>
                  {rec.confidence === 'unclear' && <Chip size="small" label="unclear" variant="outlined" color="warning" />}
                  {sourced && <Source sentence={rec.source_sentence as string} grounded={rec.grounded as boolean | null} />}
                  <IconButton aria-label={`Remove from ${title}`} onClick={() => onChange(items.filter((_, j) => j !== i))}>
                    <DeleteOutline fontSize="small" />
                  </IconButton>
                </Stack>
              </Stack>
              {sourced && (
                <TextField
                  size="small"
                  variant="standard"
                  fullWidth
                  label="Source sentence from the transcript"
                  value={(rec.source_sentence as string) ?? ''}
                  onChange={(e) => update(i, 'source_sentence' as keyof T, e.target.value)}
                  sx={{ mt: 1 }}
                  slotProps={{ input: { sx: { fontFamily: '"Lora", serif', fontSize: '0.9rem', fontStyle: 'italic' } } }}
                />
              )}
            </Box>
          )
        })}
      </Stack>
      <Button size="small" startIcon={<Add />} onClick={() => onChange([...items, { ...empty }])} sx={{ mt: 1 }}>
        Add
      </Button>
    </Box>
  )
}
