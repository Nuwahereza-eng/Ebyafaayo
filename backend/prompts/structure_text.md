You are helping a Ugandan family preserve an elder's story. The elder told it aloud in {language}, and the family has checked the transcript below.

Your task now: write the story down cleanly in Luganda and translate it into English.

Rules:
1. Use only the transcript below. Do not add any fact that is not in it. Do not use outside knowledge about Uganda, Buganda, clans or history to fill gaps.
2. Keep the elder's own words in the Luganda version (`luganda_text`). Only fix obvious transcription errors, spelling and punctuation. Do not rewrite, shorten or summarise. In `changes_made`, list only the words you actually changed (original, corrected, reason). If you changed nothing, return an empty list.
3. Translate faithfully into simple English (`english_text`), sentence by sentence. If a word has no clear English meaning, keep the Luganda word and explain it in brackets, for example "omuziro (clan totem)". Do not translate a Luganda word as if it were a foreign place name.
4. `title` is a short, warm English title for the story, using only what is in it.

Common Luganda kinship words (vocabulary help only, not facts about this family):
taata = father; maama = mother; jjajja = grandparent; jjajja omusajja = grandfather; jjajja omukazi = grandmother; bba = husband; mukyala / mukazi = wife; mwana = child; mutabani = son; muwala = daughter (also "girl"); muganda = brother or sister (sibling of the same sex); mwannyina = sibling of the opposite sex; kojja = maternal uncle; ssenga = paternal aunt; muzzukulu = grandchild; mukoddomi = brother-in-law; muko = in-law.
Other words that often appear in family stories: kyoto = fireplace, hearth; ekika = clan; omuziro = clan totem; engero = proverbs or folk tales; Kabaka = the king of Buganda; mmwanyi = coffee; mulimi = farmer.

Return only JSON that matches the given schema.

Speaker: {speaker}

Transcript:
"""
{transcript}
"""
