# Agent session log

A short log of the main steps and decisions made while building Ebyafaayo with an AI coding agent (Claude Code), for the challenge's "share your agent session" option.

## 30 October 2026

**Checking the laptop.** ThinkPad T470s: i5-7300U (4 threads), 7.6 GB RAM (about 2 GB free with VS Code and a browser open), no GPU, 3.1 GB of free disk space. Node came from nvm. Ollama was not installed, and there was no Hugging Face login.

**Decision: Gemma 4 E2B, not E4B.** E4B is 6.6 GB in Ollama and does not fit in RAM next to anything else on this laptop. The 26B and 31B models are out of reach.

**Decision: run the Sunbird model through faster-whisper int8.** `Sunbird/asr-whisper-large-v3-salt` is 6.2 GB of float32 weights, which needs about 6 GB of RAM in transformers and is very slow on this CPU. Converting it once to CTranslate2 int8 brings it to about 1.6 GB and makes it several times faster. It is still the same Sunbird weights, quantised. Nobody had published a conversion, so `scripts/convert_asr.py` does it. It loads the weights as float16 to save RAM, saves the model's own `tokenizer.json` (otherwise faster-whisper quietly downloads a different tokenizer from the internet), and then deletes the 6.2 GB original.

**Language token.** It is taken from the Sunbird model card (Luganda = 50355), not guessed. The conversion script maps it to a Whisper language code through the model's own tokenizer and writes the mapping to `salt_languages.json`.

**Freeing disk space.** Clearing the npm and pip download caches freed about 9 GB.

**Installing Ollama without sudo.** The official archive is 1.5 GB, most of it GPU libraries. It was streamed straight through `zstd | tar`, keeping only the CPU build (76 MB), into `~/.local/ollama`.

**Out of memory.** The first Gemma test was killed by the Linux out-of-memory killer (`llama-server`, 3.7 GB, while only about 2.8 GB was free), and it took the agent's editor session down with it. Lessons:
- The app runs one heavy job at a time (a single worker thread).
- It unloads Gemma (`keep_alive: 0`) before transcribing and drops the speech model after.
- The README tells people to close heavy apps on 8 GB machines.

**Honesty by construction, not only by prompt.** The structure prompt tells Gemma to use only the transcript, never to guess clans, totems, names, dates or relationships, and to quote its source sentence for every item. A small model can still drift, so `grounding.py` checks every quote against the transcript:
- A matching quote is replaced with the exact transcript sentence.
- A quote or name that cannot be found is marked "unclear" and highlighted for the family.
- A clan or totem that is not in the transcript is removed.

Unit tests cover an invented uncle and an invented clan.

**Structured output.** Ollama's `format` takes a JSON schema generated from the Pydantic model, so Gemma is constrained to the right shape. Pydantic validates the result, with one "fix this JSON" retry. The response is streamed so the UI can show progress, because generation takes minutes on a CPU.

**Consent.** A recording cannot be created without the consent checkbox and the name of the family member who asked. The exact consent text is stored with the recording. Tested.

**Fallback.** If the speech model is not installed, the family can listen and type the transcript. The rest of the flow works the same.

**Two crashes, one cause.** Ollama had been started from inside VS Code's process group, so when memory ran out, the system killed that whole group, editor included. Ollama now runs as its own temporary systemd user service with a memory cap (`systemd-run --user -p MemoryMax=4800M ...`). If it runs out, only Ollama stops.

**First real Gemma result (sample story, one call, 210 s).** The Luganda was kept exactly and no clan was invented. But the translation had serious errors ("ku kyoto", by the fireplace, became "in Kyoto"; "mulimi wa mmwanyi", coffee farmer, became "water carrier"), every relationship was left empty, no places were listed, and `changes_made` was full of entries that changed nothing.

**Second try (better prompt).** We added a kinship glossary to the prompt, as vocabulary help rather than facts, an explicit rule to list places, and a filter for no-op changes. The translation improved a lot, but this time Gemma returned *every* list empty.

**Decision: two focused calls, with every field required.** One call writes the text and translation; the other extracts. Now it found all four people with correct relationships, all three places, both times and the proverb. Everything matched the transcript, in 170–235 s.

**A runaway loop.** In the app, the extraction call once looped for 8+ minutes ("ekyera ekyera ekyera ..."). The fix was a `maxLength` on every string and a `maxItems` on every list in the JSON schema, which Ollama enforces while Gemma writes, plus a `num_predict` cap. The next run finished in 170 s.

**Honest limits found in testing.** E2B's translation once turned "I met my husband" into "my husband was killed", and it never got the proverb's meaning right. The grounding check cannot catch translation errors, so the README says so plainly and the UI asks for a bilingual check.

**Gemma audio test: cut.** Gemma 4 E2B in Ollama has no audio input, and testing it through transformers needs another ~10 GB download that this laptop cannot hold.
