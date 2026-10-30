export type Confidence = 'clear' | 'unclear'

export interface Person {
  id: number
  name: string
  relationship: string
  years: string
  about: string
  story_count: number
  photo_url: string | null
}

export interface Recording {
  id: number
  person_id: number
  speaker_name: string
  language: string
  status: 'uploaded' | 'queued' | 'transcribing' | 'transcribed' | 'failed'
  progress: number
  error: string
  duration_s: number
  transcript_raw: string
  transcript: string
  transcript_reviewed: boolean
  consent_text: string
  consent_recorded_by: string
  consent_at: string
  created_at: string
  memory_id: number | null
  person: Person
}

export interface Sourced {
  source_sentence: string
  grounded?: boolean | null
}
export interface PersonMention extends Sourced {
  name: string
  relationship_to_speaker: string | null
  confidence: Confidence
}
export interface PlaceMention extends Sourced {
  name: string
  confidence: Confidence
}
export interface TimePeriod extends Sourced {
  description: string
  confidence: Confidence
}
export interface Attribute extends Sourced {
  value: string
}
export interface Proverb extends Sourced {
  luganda: string
  english: string
}
export interface Question {
  luganda: string
  english: string
  answered?: boolean
}
export interface Change {
  original: string
  corrected: string
  reason: string
}

export interface MemoryData {
  title: string
  luganda_text: string
  english_text: string
  changes_made: Change[]
  people: PersonMention[]
  places: PlaceMention[]
  time_periods: TimePeriod[]
  clan: Attribute | null
  totem: Attribute | null
  proverbs: Proverb[]
  follow_up_questions: Question[]
  notes?: string[]
  luganda_similarity?: number
  retried?: boolean
}

export interface Memory {
  id: number
  recording_id: number
  person_id: number
  status: 'generating' | 'draft' | 'saved' | 'failed'
  progress_chars: number
  error: string
  model: string
  generation_seconds: number
  title: string
  data: MemoryData
  transcript: string
  speaker_name: string
  language: string
  duration_s: number
  recorded_at: string
  consent_text: string
  consent_recorded_by: string
  created_at: string
  person: Person
}

export interface TimelineEntry {
  year: number | null
  description: string
  source_sentence: string
  memory_id: number
  title: string
}

export interface MentionSummary {
  name: string
  relationships?: string[]
  stories: { memory_id: number; title: string; source_sentence: string }[]
}

export interface FamilyPhoto {
  id: number
  person_id: number
  url: string
  caption: string
  status: 'describing' | 'ready' | 'failed'
  progress_chars: number
  error: string
  model: string
  generation_seconds: number
  description: string
  questions: Question[]
  notes: string[]
  created_at: string
}

export interface Remembrance {
  person: Person
  memories: Memory[]
  people: MentionSummary[]
  places: MentionSummary[]
  timeline: TimelineEntry[]
  open_questions: (Question & { memory_id: number; index: number; title: string })[]
  photos: FamilyPhoto[]
}

export interface Draft {
  recording_id: number
  status: Recording['status']
  created_at: string
  memory_id: number | null
  memory_status: Memory['status'] | null
  preview: string
}

export interface Status {
  asr: { model: string; ready: boolean }
  gemma: { running: boolean; model: string; model_ready: boolean }
  jobs: { engine: 'temporal' | 'thread'; address: string; error: string }
  languages: Record<string, string>
  consent_text: string
  privacy: string
}

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method }
  if (body instanceof FormData) init.body = body
  else if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers = { 'Content-Type': 'application/json' }
  }
  const res = await fetch(url, init)
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try {
      const j = await res.json()
      if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch {
      /* not JSON */
    }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export const api = {
  status: () => request<Status>('GET', '/api/status'),
  people: () => request<Person[]>('GET', '/api/people'),
  createPerson: (p: Partial<Person>) => request<Person>('POST', '/api/people', p),
  updatePerson: (id: number, p: Partial<Person>) => request<Person>('PATCH', `/api/people/${id}`, p),
  uploadPhoto: (id: number, file: File) => {
    const f = new FormData()
    f.append('photo', file)
    return request<Person>('POST', `/api/people/${id}/photo`, f)
  },
  createRecording: (f: FormData) => request<Recording>('POST', '/api/recordings', f),
  recording: (id: number) => request<Recording>('GET', `/api/recordings/${id}`),
  saveTranscript: (id: number, transcript: string) =>
    request<Recording>('PATCH', `/api/recordings/${id}/transcript`, { transcript }),
  retryTranscription: (id: number) => request<Recording>('POST', `/api/recordings/${id}/transcribe`),
  deleteRecording: (id: number) => request<{ ok: boolean }>('DELETE', `/api/recordings/${id}`),
  structure: (recId: number) => request<Memory>('POST', `/api/recordings/${recId}/structure`),
  memory: (id: number) => request<Memory>('GET', `/api/memories/${id}`),
  updateMemory: (id: number, title: string, data: MemoryData, save: boolean) =>
    request<Memory>('PATCH', `/api/memories/${id}`, { title, data, save }),
  markQuestion: (memId: number, index: number, answered: boolean) =>
    request('PATCH', `/api/memories/${memId}/questions/${index}`, { answered }),
  addFamilyPhoto: (personId: number, file: File) => {
    const f = new FormData()
    f.append('photo', file)
    return request<FamilyPhoto>('POST', `/api/people/${personId}/photos`, f)
  },
  familyPhoto: (id: number) => request<FamilyPhoto>('GET', `/api/photos/${id}`),
  updateFamilyPhoto: (id: number, p: Pick<FamilyPhoto, 'caption' | 'description' | 'questions'>) =>
    request<FamilyPhoto>('PATCH', `/api/photos/${id}`, p),
  describeFamilyPhoto: (id: number) => request<FamilyPhoto>('POST', `/api/photos/${id}/describe`),
  deleteFamilyPhoto: (id: number) => request<{ ok: boolean }>('DELETE', `/api/photos/${id}`),
  remembrance: (personId: number) => request<Remembrance>('GET', `/api/people/${personId}/remembrance`),
  drafts: (personId: number) => request<Draft[]>('GET', `/api/people/${personId}/drafts`),
  book: (personId?: number) => request<Remembrance[]>('GET', personId ? `/api/book?person_id=${personId}` : '/api/book'),
}

export const audioUrl = (recId: number) => `/api/recordings/${recId}/audio`

export function formatDate(iso: string) {
  return new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z').toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
