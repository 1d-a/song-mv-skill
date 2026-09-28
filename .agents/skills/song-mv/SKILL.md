---
name: song-mv
description: Turn a song (audio + lyrics + opening title/subtitle) into a polished vertical lyric music video for 抖音/快手/B站 with no human characters. Produces three style previews (水墨江湖 / 蜡笔童画 / 剪纸月夜), waits for the user to pick one, then renders the full video.
---

# song-mv: 歌曲 → 无人物歌词 MV

Repo: https://github.com/1d-a/song-mv-skill (toolkit `mvkit/`, fonts, full example `examples/mujian/`).

## Hard requirements (from the user — never violate)
- **No people / characters acting out a plot.** Tell the story with objects (木剑、破衫、火药包、红线…), landscape, weather, sun/moon, text glyphs, camera moves and beat effects.
- **The sung sections must keep changing visually, like the intro does.** Not just lyrics over a static backdrop: a new scene (mood change / page / wipe) every ~2 lines and at least one new event per line. `python -m mvkit.storyboard PROJECT` must print `no problems found`.
- Lyrics appear per character at the **actual sung time** (from `mvkit.align`), not evenly spread.
- Output: 1080×1920, 30 fps, H.264 + original audio (AAC), full song length.
- Opening title + subtitle are shown in the chosen style's own typography during the intro — nothing else in the intro (no lyric teaser, credits or seal unless the user asks; set `"credits": ""`, `"seal": ""`).
- No on-screen text that isn't sung: `[...]` tags are performance cues, never shown; `stamp`/glyph/pouch texts must be words from the lyrics sung at that moment.
- Chorus / climax lyrics get a dedicated `lyricfx` treatment matching the section's mood (`bold` confident, `fragile` vulnerable, `tragic` heavy resolve, `rise` crescendo, `final` biggest: giant slamming characters, flash, shake, rays). Currently implemented in `crayon`.
- `crayon` also supports a picture-book `shots` storyboard (see `mvkit/styles/crayon_book.py`, assets in `crayon_art.py`): every lyric pair/line gets its own page with its own background and an explicit item list; nothing carries over between pages. Draw the concrete objects the lyric names (bridge, abyss, bread, talisman, altar, crane, book, statue, bowl, smoke...) -- never a generic ring-with-a-word. Check every page with a keyframe sheet before the full render.

## Inputs to collect
Audio file, lyrics (text/file, `[Verse]`-style tags allowed), opening title, opening subtitle. Optional: credits line (default `词曲 · 演唱`), seal text for 水墨 (default = first 4 chars of title). If any of the four required inputs is missing, ask for it before starting.

## Procedure
1. Setup (once per machine): `cd song-mv-skill && ./setup.sh` (needs ffmpeg; downloads faster-whisper `small`). Use `PY=.venv/bin/python`, run commands from the repo root.
2. Create `projects/<slug>/` with `song.mp3` (copy/convert the audio), `lyrics.txt`, and `project.json`:
   `{"audio":"song.mp3","lyrics_file":"lyrics.txt","title":"…","subtitle":"…","credits":"词曲 · 演唱","seal":"…"}`
   Optional keys: `drop` (seconds the beat kicks in, auto-detected otherwise), `title_out`.
3. Align: `$PY -m mvkit.align projects/<slug>` → `lyrics.json`. Check the printed table: every line has a time, times increase, and `conf` values are mostly ≥0.8. For lines with low conf or clearly wrong times, listen around that point (`ffmpeg -ss … -t 6`) or re-check neighbours and hand-edit `times` in `lyrics.json` (one float per character, `end` = last char + ~0.4 s).
4. Storyboard: `$PY -m mvkit.storyboard projects/<slug> --draft` writes `storyboard.draft.json` from lyric keywords. **Rewrite it by hand into `storyboard.json`**, reading the lyrics like a director:
   - one `scenes` entry about every 2 lines, at section changes, and where the emotion shifts; pick `mood` from default/day/dawn/dusk/night/storm to match the lyrics;
   - for every line, add at least one event that illustrates a noun/verb in that line (`prop` with shape sword/pouch/cloak/fire/glyph, `clouds`, `dim`, `village`, `thread`, `burst`, `thunder`, `scatter`, `fireworks`, `lanterns`, `stamp`, `weather`, `zoom`); use `glyph` with a key character for abstract words;
   - anchor events to lyrics with refs like `L5`, `L5.3`, `L5.end+0.5`, and hits like `chars:L8`, `strong:L85~L88.end`;
   - big moments (chorus peaks, climax) get thunder/stamp/fireworks; quiet sections get weather, dim, slow zoom.
   Syntax and a full-song example: README.md and `examples/mujian/storyboard.json`. Re-run `$PY -m mvkit.storyboard projects/<slug>` until it prints `no problems found`.
5. Three previews: `$PY -m mvkit.preview projects/<slug> --clip 8` → `out/方案A_水墨江湖.jpg`, `out/方案B_蜡笔童画.jpg`, `out/方案C_剪纸月夜.jpg` (8 key frames each, the same moments across styles) plus an 8-second clip of the busiest stretch per style. View the sheets yourself first (overlaps, unreadable lyrics, a prop covering the title); fix the storyboard (e.g. add `pos`) and regenerate if needed.
6. Send the three sheets (and clips) to the user in one message, briefly describing each style, and **wait for them to choose** (A/B/C, or change requests). Do not start the full render before they choose.
7. Full render: `$PY -m mvkit.render projects/<slug> --style ink|crayon|paper` (A=ink, B=crayon, C=paper). It renders 10 s chunks in parallel (`--jobs`, default half the CPUs) and caches them in `build/<style>/`; if interrupted, rerun the same command to resume. It's slow on CPU (roughly 1–2 s per frame per core; a 5-minute song takes a few hours on 2 cores), so run it in the background with `nohup … > render.log 2>&1 &` and poll the log. For a quick check first, render `--dur 33`.
8. Verify: the render prints `duration / size / streams … OK` (ffprobe). Also extract 6–8 stills across the song (`--stills t1,t2,… --sheet check.png`) and look at them. Then send the MP4 to the user (a file over ~100 MB can be split or re-encoded with a higher `-crf` if the upload fails).

## Style keys
| key | 方案 | Look |
|---|---|---|
| `ink` | 水墨江湖 | rice paper, parallax ink mountains, mist, red sun, vertical brush-written lyrics, brush wipe between scenes |
| `crayon` | 蜡笔童画 | crayon picture book, one page per scene with page-turn, wobbling hand-drawn lines, handwritten lyrics |
| `paper` | 剪纸月夜 | layered paper-cut moonlit valley, cliffs + rope bridge + village, red paper lyric tiles |

## Adding a style
Create `mvkit/styles/<key>.py` with `class Style` (`__init__(self, P)`, `frame(self, t) -> HxWx3 float array`), read only `P.scenes`, `P.events`, `P.lyric_state(t)`, `P.beat(t)`, `P.mood_at()`, and register it in `mvkit/styles/__init__.py`. Support every event type in `mvkit/storyboard.TYPES` (at least with a simple fallback).
