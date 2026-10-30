# Demo video plan (about 2 minutes)

The goal: show that a family can record an elder, check the words, and get a memory they control, all on one laptop with the internet off.

## 1. Prepare (30 to 45 minutes, the day before if you can)

**Stories.** You need three real Luganda recordings, each 30 to 60 seconds long. Each speaker has to agree to be recorded and shown in a public video.

- **Two stories to save before you film**, so the remembrance page, timeline and memory book are already full. Short stories with names, places and a year work best: who their parents were, where they were born, a move during a hard time, a proverb they grew up with.
- **One story to record during the video.**

If you can't reach an elder in time, ask a parent, an aunt or yourself to tell a story you heard from jjajja, and name the person truthfully in the app (for example "Told by Peter, about Jjajja ..."). Don't present anyone as someone they are not.

**Start from a clean app.** In a terminal:

```bash
cd ~/Ebyafaayo
systemctl --user start ebyafaayo-ollama   # Gemma's server (skip if already running)
make run                                   # then open http://127.0.0.1:8000
```

Then add the two prepared stories through the app: Record a new story → consent → upload the file → check the transcript → "Turn into a family memory" → check every field → Save. On the elder's page, use the camera button to add a photo if you have one.

**Free up memory.** Close everything except one Chrome window with the app and your screen recorder. Gemma needs about 4 GB free.

**Browser.** Use Chrome in a 1280×800 window with the zoom at 110% (Ctrl and +). Hide the bookmarks bar (Ctrl+Shift+B). The browser stays open throughout, but the address bar should only ever show `127.0.0.1`.

**Screen recorder.** Use one that records your microphone too, so you can talk while you click. SimpleScreenRecorder (`sudo apt install simplescreenrecorder`) or OBS Studio both work. If you'd rather not speak, record silently and add the lines below as captions while editing.

**Do a full practice run once,** without recording.

## 2. Film

Keep the real waiting in the recording, then speed it up or cut it while editing. Never fake the speed. The captions say how long it really took.

| Time | What to show | What to say (or show as a caption) |
|---|---|---|
| 0:00–0:12 | Home page with the elder's card. Move the mouse over it slowly. | "Ask a young person in Kampala what their clan is, and many will pause. Our history lives in our grandparents' voices, and most of it was never written down. Ebyafaayo keeps it." |
| 0:12–0:18 | Click the Wi-Fi icon in the top bar and turn Wi-Fi off. Let the "Offline" badge in the app show. | "First, I turn off the internet. Everything from here runs on this laptop." |
| 0:18–0:35 | Click **Record a new story**. Choose the elder, read the consent text out loud, type your name, tick the box. | "Before anything is recorded, we ask for consent. The app saves it with the recording." |
| 0:35–0:45 | Press **Record**, let the elder speak for 30 to 45 seconds, press **Stop**, then **Save and transcribe**. (Cut most of the speaking in editing; keep about 5 seconds.) | "Jjajja tells the story in Luganda." |
| 0:45–1:00 | The transcript page: the progress bar, then the transcript next to the audio player. Click into the text and correct one word, ideally a name. | "Sunbird AI's open Luganda speech model writes it down. Then we listen and correct it, because an elder's words matter." Caption on the progress bar: "Transcription runs on the laptop's CPU (sped up)." |
| 1:00–1:20 | Click **Turn into a family memory with Gemma**. Show "Gemma is writing the memory…", then cut to the result. | "Gemma 4 runs locally through Ollama. It writes the story in Luganda and English, and finds the people, places and times." Caption: "About 3 minutes on a 2017 laptop (sped up)." |
| 1:20–1:35 | Hover over the quote icon next to a person so the source sentence pops up. Scroll to **Clan and totem** and pause on "We never guess a clan." | "Every name points back to the exact sentence it came from. If the elder didn't say a clan or totem, Gemma is not allowed to guess one." |
| 1:35–1:42 | Correct one thing (a relationship or a word in the English), then click **Save to … remembrance page**. | "The family has the final say on everything." |
| 1:42–1:52 | The remembrance page: scroll past the stories, the timeline, the people and places, and the questions to ask next time. | "Every story builds Jjajja's remembrance page, with gentle questions to ask next time." |
| 1:52–2:00 | Click **Memory book**, then **Save as PDF**, and show the print preview. | "And a memory book we can print and share at the next family gathering." |
| 2:00–2:08 | The About page, showing both models ready and the credits. | "Open models, free to run, and in our own language. Ebyafaayo." |

Total: about 2 minutes. If it runs long, shorten the remembrance page and About shots first.

## 3. Edit

- Speed up or cut every wait: transcription, Gemma, page loads. Keep the progress screens on screen for about 2 seconds so people can see the real work happening.
- Add the two captions marked above, and a final card: "github.com/Nuwahereza-eng/ebyafaayo · Gemma 4 · Sunbird AI · Ollama".
- For the recorded story, add an English subtitle of what the elder says, so judges who don't speak Luganda can follow.
- Export at 1080p (or 720p) as MP4.

## 4. Publish

1. Upload to YouTube as **Unlisted** (or Public), titled "Ebyafaayo: keeping family stories alive with Gemma 4, offline".
2. In the DEV post, under **Demo**, add `{% youtube VIDEO_ID %}` above the screenshots.
3. Before publishing the post, watch the video once with the sound off to check the captions tell the story on their own.
