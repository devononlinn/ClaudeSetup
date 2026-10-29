I'm attaching the MP4 of my YouTube video (my own channel, "Stay On The Line Files"). Please remake the whole video's visuals as a dark pictogram horror animation, keeping my original narration, and add burned-in subtitles and sound effects. Output a 1920×1080 MP4.

## The video
- Channel: Stay On The Line Files. Series: "DO NOT PET" analog horror. Framing: callers reach the "After-Hours Animal Behavior Line"; each video is a bulletin of 7 rules.
- This is Bulletin 01: "If your dog ever waits at the window too early… do not open the door" (video ID VxpVZI34lcc). It's built on a real 1990s case: a terrier named Jaytee, filmed in 100+ trials going to the window when his owner set off for home.
- Chapters from the description (use the attached video for anything past Rule 5):
  - 0:00 Please Stay On The Line
  - 0:19 The Dog Named Jaytee
  - 1:08 Rule 1: Keep The List
  - 1:53 Rule 2: Stay Out Of The Glass
  - 2:33 Rule 3: Watch The Tail
  - 3:13 Rule 4: Let The Dog Decide
  - 3:48 Rule 5: Do Not Answer The Voice
  - …then Rules 6–7 and End Of Bulletin

## Visual style (match exactly)
- Near-black background (#000–#0a0a0a). Everything is flat, geometric pictograms:
  - Furniture and buildings: thin white outlines (~3 px), mid-grey fills.
  - Characters: solid white or dark-grey bodies with a bright white rim.
  - Animal eyes: small glowing yellow (#FFCE46) dots.
- One red accent (#EB2424) at a time, saved for the threat. It glows and pulses.
- Bloom on everything bright: blur a downscaled copy at two radii and add it back.
- Post effects on every frame:
  - film grain
  - dark edge vignette
  - subtle brightness breathing and flicker
  - occasional single-frame glitches
- Hard cuts between shots. Each cut gets 3–4 frames of glitch: RGB channel split, horizontally shifted bands, thin white noise streaks.
- Slow camera push-ins and pans within shots. No cross-fades.
- Top HUD in small grey text: "FILE 01 // STAY ON THE LINE" top-left, a running timecode 00:00:SS:FF top-right.
- Rule cards between chapters:
  - a row of 7 rounded square number tiles, the current one highlighted
  - a big "RULE N" with the rule title and a thin red underline
  - Rule 7 is shown as [CLASSIFIED]: its tile redacted or glitching
- Characters must be original: a simple terrier-like dog pictogram (side profile; ears, tail and head as separate shapes so they can animate), a faceless round-head human, house, window, door, phone. Don't copy any other channel's characters or branding.

## Subtitles
- Burned in, centred near the bottom.
- White bold sans in ALL CAPS with a slight glow; at most 2 lines and about 42 characters per line.
- Timed to the narration. Transcribe the attached audio with word timestamps (Whisper if available). Otherwise ask me for the .srt and I'll export it from YouTube Studio.
- Apply the glitch effect to subtitles on the scariest lines.

## Audio
- Keep my original narration track unchanged.
- Add sound effects under it, synthesised in code (numpy → WAV) or as clean public-domain sounds:
  - low drone bed
  - phone-line hum, clicks, a dial tone and hold beep for "please stay on the line"
  - static and glitch bursts on every glitch cut
  - a hit or thud on each rule card
  - paw taps on glass, a soft whine, a single slow door knock, a doorknob rattle
  - a heartbeat build before reveals
- Duck the SFX under the voice (sidechain compression, or about −12 dB while speech is present). Normalise the final mix to about −14 LUFS.

## Scene plan
- Plan one or more shots per narration sentence and make the action literally show what's being said. For example: dog at the window while the owner is still far away; the family list on the fridge; the dog's reflection in the glass behaving differently; tail stops wagging; dog choosing which door to stand at; a voice at the door that sounds like a family member.
- Keep each shot 2–6 s, and put every rule card on its chapter timestamp.

## Technical approach (proven to work)
- Python with Pillow and numpy:
  - Draw each frame at 2× supersampling (3840×2160) through a camera transform (world coords → screen, with zoom and pan), then downscale with LANCZOS.
  - Bloom, grain, vignette, flicker and glitch are numpy passes on the downscaled frame.
- Pipe raw RGB frames into ffmpeg (libx264, yuv420p, CRF 18). Mux with the mixed audio at the end. 30 fps is fine.
- Build shot functions `shot(t)` from a timeline list of (start, end, scene), shared by audio and subtitles, so every cut, SFX hit and subtitle lines up.

## Workflow
1. Show me the scene plan (timestamp → shot description → SFX) first.
2. Render chapter 1 only (about the first minute) with subtitles and SFX for my approval.
3. After approval, render the full video. Also give me a compressed copy small enough to download.
