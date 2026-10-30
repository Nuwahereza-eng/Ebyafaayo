import FormatQuote from '@mui/icons-material/FormatQuote'
import HelpOutline from '@mui/icons-material/HelpOutlineOutlined'
import { Box, ClickAwayListener, IconButton, Tooltip } from '@mui/material'
import { useState } from 'react'

/** Shows the transcript sentence an item came from, on hover (desktop) or tap (phone). */
export default function Source({ sentence, grounded }: { sentence: string; grounded?: boolean | null }) {
  const [open, setOpen] = useState(false)
  const unmatched = grounded === false
  const title = (
    <Box>
      {unmatched && (
        <Box component="span" sx={{ display: 'block', fontFamily: 'Inter', fontWeight: 600, mb: 0.5 }}>
          Not found in the transcript. Please check this item.
        </Box>
      )}
      {sentence ? `“${sentence}”` : 'No source sentence.'}
    </Box>
  )
  return (
    <ClickAwayListener onClickAway={() => setOpen(false)}>
      <Tooltip
        title={title}
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        enterTouchDelay={0}
        arrow
      >
        <IconButton
          size="small"
          aria-label={unmatched ? 'Source not found in transcript' : 'Show source sentence'}
          onClick={() => setOpen((o) => !o)}
          color={unmatched ? 'warning' : 'default'}
        >
          {unmatched ? <HelpOutline fontSize="small" /> : <FormatQuote fontSize="small" />}
        </IconButton>
      </Tooltip>
    </ClickAwayListener>
  )
}
