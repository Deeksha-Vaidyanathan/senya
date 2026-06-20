# SignAI — ASL Avatar Hackathon Project
## Pika Track | Team of 3

---

## The Idea

As people watch videos, an AI avatar appears alongside the video performing the content in American Sign Language (ASL). This helps deaf users who prefer sign language over captions follow along naturally.

---

## Core Strategy: Pre-generated Sign Dictionary + Runtime Assembly

Pika can't generate accurate ASL on the fly from a text prompt alone — but we work around this by **pre-generating a library of correct sign videos** using real ASL reference footage, then assembling them at runtime.

### Full Pipeline

```
Input Video
    │
    ▼
[Pika: transcribe_audio]
    │
    ▼
Text → ASL Gloss tokens (via Claude API)
    │
    ▼
Dictionary Lookup (word → Pika-generated sign clip)
    │
    ▼
[Pika: edit_concat] → assembled signing video
    │
    ▼
[Pika: edit_pip] → final video with avatar in corner
```

---

## Step 1: Build the Sign Dictionary (Do This Before the Hackathon)

This is the most important prep work.

**Source material:** Download free ASL sign videos from public dictionaries:
- [Handspeak](https://www.handspeak.com)
- [ASLU / LifePrint](https://www.lifeprint.com)
- [ASL University](https://www.asluniversity.com)

Target **300–500 of the most common English words** to start.

**Use Pika's `generate_reference_video`** — pass the real ASL video as a motion reference and generate a consistent-looking avatar doing the same sign. Pika doesn't need to *know* ASL — it just copies the motion from reference footage onto the avatar.

```
real_asl_video["hello"]
  → generate_reference_video(
      reference=real_asl_video,
      prompt="person signing hello in ASL, clean background"
    )
  → avatar_sign["hello"].mp4
```

Store all generated clips in a hosted asset store (Supabase or S3). That's the dictionary.

---

## Step 2: Create a Consistent Avatar Character

Before building the dictionary, design the avatar once:

1. Use Pika's `generate_image` to create a base character — consistent appearance, neutral background, clear hands
2. Use that same image as the base for **every** `generate_reference_video` call
3. Consistency is critical so `edit_concat` doesn't look jarring between signs

---

## Step 3: Gloss Translation at Runtime

ASL is not word-for-word English — it has its own grammar called **ASL gloss**.

**Recommended approach:** Use the Claude API to convert the transcript to ASL gloss order before dictionary lookup. This is ~10 lines of code and makes the output significantly more accurate.

Example prompt:
```
Convert this English sentence to ASL gloss order (no articles, topic-comment structure):
"The dog ran through the field"
→ "DOG RUN THROUGH FIELD"
```

**Fallback (simpler):** Signed Exact English (SEE) — sign each English word in order. Not true ASL grammar, but visually understandable and totally shippable for a demo.

---

## Step 4: Runtime Assembly with Pika

```python
# Pseudocode
transcript = pika.transcribe_audio(video)
gloss_tokens = claude.to_asl_gloss(transcript)   # ["DOG", "RUN", "THROUGH", "FIELD"]

sign_clips = [dictionary[token] for token in gloss_tokens if token in dictionary]
# For unknown words: skip or call generate_video with a fallback prompt

signing_video = pika.edit_concat(sign_clips)
final_output  = pika.edit_pip(original_video, signing_video, position="bottom-right")
```

---

## Pika Tools Used (5 tools — strong track integration story)

| Tool | Purpose |
|------|---------|
| `transcribe_audio` | Pull transcript from input video |
| `generate_image` | Create the consistent avatar character |
| `generate_reference_video` | Build sign dictionary from real ASL reference clips |
| `edit_concat` | Assemble individual sign clips into a continuous signing video |
| `edit_pip` | Overlay the signing avatar onto the original video |

---

## Other Tools to Integrate

| Tool | Purpose |
|------|---------|
| **Claude API** | English → ASL gloss conversion (10-line prompt, big quality boost) |
| **Supabase or S3** | Host pre-generated sign dictionary for fast runtime lookup |
| **FFmpeg / Pika normalize** | Ensure all sign clips share the same frame rate and resolution before concat |

---

## Team Split

| Person | Owns |
|--------|------|
| **Person 1** | Dictionary builder — pre-generate sign clips using Pika reference video tool, manage the asset library |
| **Person 2** | Backend pipeline — transcription, gloss conversion (Claude), dictionary lookup, Pika assembly calls |
| **Person 3** | Frontend — web app UI, video upload / URL input, playback of final output, demo polish |

---

## Scope & Decisions

- **Sign language:** ASL only (v1)
- **Interface:** Web app — user uploads video or pastes URL, gets processed output
- **Gloss:** Claude-powered English → ASL gloss (with SEE fallback)
- **Avatar style:** Consistent Pika-generated character (not a third-party avatar API) — we own the full pipeline
- **Dictionary size target:** 300–500 most common words pre-generated before the event

---

## Hackathon Pitch

> "We used Pika as the full media stack for a deaf accessibility tool — transcription, avatar generation, video assembly, and final composition — all chained together to make any video instantly accessible in sign language."

---

## Open Questions (Discuss with Team)

- [ ] What do we do for words not in the dictionary? Skip, fingerspell, or generate on-the-fly?
- [ ] Should the avatar pip be bottom-right corner or side-by-side split screen?
- [ ] Do we want to support video URL input (YouTube) or upload only for the demo?
- [ ] Who owns the dictionary pre-generation work before the hackathon starts?
- [ ] What's our fallback if `generate_reference_video` motion transfer isn't clean enough?
