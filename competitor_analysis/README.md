# Competitor sound & colour analysis (analog horror)

## Status (2026-10-28)

**Not run on the real videos yet.** The cloud session's network policy blocks
YouTube video/caption downloads (`www.youtube.com`, `*.googlevideo.com`) and the
Demucs model weights (`dl.fbaipublicfiles.com`). Only the YouTube Data API was
reachable, so the video selection below is real. The analysis pipeline has been
tested end to end on a synthetic clip with known events: all six planted hit types,
the bed dropout, the silence, the red flash and the blue tint were detected and
labelled correctly.

To get the report, either allow those hosts in the cloud environment's network
settings, or run it locally (below).

## Selected videos (2 most-viewed long-form per channel, from the Data API)

| channel | video | views | length |
|---|---|---|---|
| @BradikininVideos | [If Your Dog Ever Stands On Two Legs… ACT NORMAL](https://www.youtube.com/watch?v=Vpw2D6LsIV0) | 2,840,101 | 4:33 |
| @BradikininVideos | [If Your Phone Ever Charges To 101%… DO NOT UNPLUG IT](https://www.youtube.com/watch?v=1eKx2HunTbU) | 2,008,615 | 4:41 |
| @Final_Sight | [If You See A Deer In Your Window... LEAVE THE HOUSE](https://www.youtube.com/watch?v=3r18mWU4Rx4) | 1,019,340 | 6:50 |
| @Final_Sight | [If The Whole Theater Laughs At The Wrong Part... DO NOT LAUGH](https://www.youtube.com/watch?v=PgfTx8Kmto4) | 608,928 | 10:20 |
| @Pictofear | [If Your Dog Ever Hides Under Your Bed at 2 AM… GET UNDER THERE WITH IT](https://www.youtube.com/watch?v=jlvRzp9OKrM) | 575,424 | 10:19 |
| @Pictofear | [If Your Dog Ever Barks at an Empty Corner… DO NOT LOOK](https://www.youtube.com/watch?v=U3ULUZUbYmU) | 84,757 | 10:14 |
| @CastVenk | [If You See Two Moons in the Sky… DON'T LOOK UP](https://www.youtube.com/watch?v=uZvn_d6eT_k) | 100,443 | 10:22 |
| @CastVenk | [If Your Mom Does This, Leave Your House Immediately](https://www.youtube.com/watch?v=1k4bedfpR9Y) | 56,425 | 8:04 |
| @ResidentAdvisory | [If Your Cat Ever Screams Like A Person… DO NOT GO OUTSIDE](https://www.youtube.com/watch?v=zRRiyoSOfGk) | 32,526 | 4:53 |
| @ResidentAdvisory | [If Your Dog Ever Comes Home With No Collar… DO NOT LET IT IN](https://www.youtube.com/watch?v=aYEDZxKyNxw) | 18,830 | 4:02 |
| @Odd_Hours1 | [If The Whole Class Stops Talking... STOP TALKING](https://www.youtube.com/watch?v=wsHBmFfzTe4) | 26,091 | 7:00 |
| @Odd_Hours1 | [If Your Grandma Ever Calls At 3 AM… DON'T PICK UP](https://www.youtube.com/watch?v=5oDsQv_kYhU) | 17,660 | 7:36 |
| @dreadifymain | [If You Hear Purring Under Your Blanket But Your Cat Is In The Doorway.](https://www.youtube.com/watch?v=OU3mLHNdPGA) | 23,021 | 8:23 |
| @dreadifymain | [If Your Dog Ever Comes Back From The Yard And He's Not Alone...](https://www.youtube.com/watch?v=oWLqVgH5pl8) | 11,274 | 8:03 |
| @deadairvhs | [If Your Dog Starts Barking at Night… LOCK The Door](https://www.youtube.com/watch?v=rLCcir7FgLc) | 20,547 | 4:13 |
| @deadairvhs | [If Your Dog Starts Smiling At You… LOCK The Door](https://www.youtube.com/watch?v=E-buyTMylKc) | 15,576 | 6:04 |

**@TheSonuFiles-y1r** ("Under the Lid", 506 subs) has no public videos (API `videoCount: 0`),
so it is left out. Long-form means longer than 3 min and no `#shorts` in the title.
Full metadata is in `picks.json`.

Already visible from the metadata: almost every video uses the same title formula,
"If [ordinary thing] does [wrong thing]… [IMPERATIVE IN CAPS]". Bradikinin's two
videos (2.0–2.8M views) are only about 4.5 minutes long. Final Sight and Pictofear
reach 0.6–1M views with 7–10-minute videos. The other six channels are all under 100k.

## Running it

```bash
pip install yt-dlp librosa nltk soundfile scipy numpy demucs   # demucs pulls torch
python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"
# needs ffmpeg/ffprobe on PATH
python analyze.py --picks picks.json --out out/
# -> out/report.md, out/hits.csv, out/color.csv, out/frames/, out/competitor_sound_color.zip
```

To pick videos again: `YT_API_KEY=... python pick_videos.py @BradikininVideos ... > picks.json`.

Videos are downloaded into a temp folder and deleted after each one is analysed
(`--keep-video` keeps them). Per-video results are cached in `out/cache/`, so an
interrupted run picks up where it stopped. `--report-only` rebuilds the report and
zip from the cache. On CPU, Demucs takes roughly 1–2× real time, so expect about 2 h
for all 16 videos.

## Method notes for whoever reads the report

- **Hits:** stretches of the non-voice stem that peak ≥6 dB above a rolling bed
  (30th percentile over 3 s), split at librosa onsets. Steady music and ambience
  stay near the bed, so they are ignored. The level is peak RMS minus the narrator's
  median speaking RMS.
- **Categories** come from rules on low-band share (<150 Hz), flatness, attack, where
  the peak falls, centroid slope and abrupt gating. They are approximate. Spot-check
  the loudest hits listed in each video's section.
- **Words:** auto-captions have no punctuation, so "sentence end" means the word is
  followed by a pause of 0.6 s or more. "Number" includes number words and the words
  "rule" and "number".
- **Visuals:** frames are sampled every 0.5 s, so sound/visual coincidence uses
  ±0.2 s plus half a frame step (±0.45 s in total).
- The 10 rules in the report are drafts generated from the top-performer numbers.
  Edit them before using.
