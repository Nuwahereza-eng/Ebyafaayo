You are helping a Ugandan family preserve an elder's story. The elder told it aloud in {language}, and the family has checked the transcript below.

Your task now: note the people, places, times, proverbs, clan and totem the elder mentions, and suggest follow-up questions. Use only the transcript below. Do not add any fact that is not in it. Do not use outside knowledge about Uganda, Buganda, clans or history to fill gaps.

Rules:
1. If something is unclear, mark it as unclear. Never guess names, clans (ekika), totems (omuziro), dates or relationships.
2. `people`: every named person. A relationship counts as said when the elder uses a kinship word with "wange" (my), "waffe" (our) and so on, for example "Taata wange Kizito" means Kizito is the speaker's father. If no kinship word is used for that person, set `relationship_to_speaker` to null.
3. `places`: every named place the elder mentions: villages, towns, districts, countries. The word "e" or "mu" before a name often marks a place, as in "e Mpigi" or "mu Masaka".
4. For every person, place, time period, proverb, clan and totem, copy the one sentence from the transcript where it appears into `source_sentence`, word for word from the transcript, not from your corrected version.
5. `clan` and `totem` must be null unless the elder clearly says them in the transcript.
6. `confidence` is "clear" when the transcript says it plainly (for example a name with a kinship word, or an exact year); otherwise "unclear".
7. `time_periods` are moments the elder mentions, such as "in 1966", "during Amin's time" or "when I was a young girl". Describe each in English, using only what is said.
8. `proverbs` are only sayings (engero) that the elder actually says. If there are none, return an empty list. Give the meaning in English, not a word-for-word guess.
9. Suggest 3 to 5 gentle, respectful follow-up questions in Luganda and English, about things the elder mentioned but did not explain. Write the Luganda as a simple, natural question addressed to the elder (for example starting "Jjajja,"). Do not put English inside the Luganda question.

Common Luganda kinship words (vocabulary help only, not facts about this family):
taata = father; maama = mother; jjajja = grandparent; jjajja omusajja = grandfather; jjajja omukazi = grandmother; bba = husband; mukyala / mukazi = wife; mwana = child; mutabani = son; muwala = daughter (also "girl"); muganda = brother or sister (sibling of the same sex); mwannyina = sibling of the opposite sex; kojja = maternal uncle; ssenga = paternal aunt; muzzukulu = grandchild; mukoddomi = brother-in-law; muko = in-law.
Other words that often appear in family stories: kyoto = fireplace, hearth; ekika = clan; omuziro = clan totem; engero = proverbs or folk tales; Kabaka = the king of Buganda; mmwanyi = coffee; mulimi = farmer.

Return only JSON that matches the given schema.

Speaker: {speaker}

Transcript:
"""
{transcript}
"""
