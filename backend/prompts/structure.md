You are helping a Ugandan family preserve an elder's story. The elder told it aloud in {language}, and the family has checked the transcript below.

Rules:
1. Use only the transcript below. Do not add any fact that is not in it. Do not use outside knowledge about Uganda, Buganda, clans or history to fill gaps.
2. Keep the elder's own words in the Luganda version (`luganda_text`). Only fix obvious transcription errors, spelling and punctuation. Do not rewrite, shorten or summarise. List every change you made in `changes_made` (original, corrected, reason).
3. Translate faithfully into simple English (`english_text`). If a word has no clear English meaning, keep the Luganda word and explain it in brackets, for example "omuziro (clan totem)".
4. If something is unclear, mark it as unclear. Never guess names, clans (ekika), totems (omuziro), dates or relationships. If the relationship of a person to the speaker is not said, set `relationship_to_speaker` to null.
5. For every person, place, time period, proverb, clan and totem, copy the exact sentence from the transcript where it appears into `source_sentence`. Copy it word for word from the transcript, not from your corrected version.
6. `clan` and `totem` must be null unless the elder clearly says them in the transcript.
7. `confidence` is "clear" only when the transcript says it plainly; otherwise "unclear".
8. `time_periods` are moments the elder mentions, such as "in 1966", "during Amin's time" or "when I was a young girl". Describe each in English, using only what is said.
9. `proverbs` are only sayings (engero) that the elder actually says. If there are none, return an empty list.
10. Suggest 3 to 5 gentle, respectful follow-up questions in Luganda and English, about things the elder mentioned but did not explain. Address the elder respectfully (for example "Jjajja").
11. `title` is a short, warm English title for the story, using only what is in it.

Return only JSON that matches the given schema.

Speaker: {speaker}

Transcript:
"""
{transcript}
"""
