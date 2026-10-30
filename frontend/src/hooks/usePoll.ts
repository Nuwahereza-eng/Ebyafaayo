import { useEffect, useRef } from 'react'

/** Calls `fn` every `ms` while `active` is true. */
export function usePoll(fn: () => void, active: boolean, ms = 2000) {
  const saved = useRef(fn)
  saved.current = fn
  useEffect(() => {
    if (!active) return
    const t = setInterval(() => saved.current(), ms)
    return () => clearInterval(t)
  }, [active, ms])
}
