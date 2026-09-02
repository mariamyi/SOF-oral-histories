# Souls on Fire — CollectionBuilder-OH Setup Design

Date: 2026-09-02

## Background

The Calfee Community and Cultural Center's "Souls on Fire: Gospel Traditions and
Community Organizing in Pulaski, VA" project documents Black Appalachian gospel
music, churches, and activism (including the former NAACP Pulaski Branch) in
Pulaski County, VA. Over 100 oral histories have been conducted under the
project's African American Heritage Center umbrella. The project's Mellon
Foundation proposal describes an eventual public exhibit on WordPress with
KnightLab tools; this repo is a parallel exploration of CollectionBuilder-OH
(CB-OH) as an alternative/prototype platform, chosen specifically for its
color-coded thematic transcript visualization synced to interview audio.

An existing, unrelated repo (`mariamyi/soulsonfire`) already uses the
CollectionBuilder-Sheets template for other work and is left untouched.

## Repository

- **New repo:** [mariamyi/SOF-oral-histories](https://github.com/mariamyi/SOF-oral-histories),
  created from the [oralhistoryasdata/template](https://github.com/oralhistoryasdata/template)
  (CB-OH) GitHub template. Public.
- Cloned locally to `/Users/mariamyi/Downloads/SOF-oral-histories`, fully
  independent Jekyll site/build/config from `soulsonfire`.
- Raw source materials (original transcripts, audio) staged outside any git
  repo at `/Users/mariamyi/Downloads/SOF-oral-histories-source/` to avoid
  committing large/unprocessed files before they're ready.

## Content: initial interviews

Two interviews to start (of an eventual larger set):

1. **Patricia Poole** — interviewed by Clay Adkins, ~24 min. Topics: NAACP era
   school integration at Pulaski High School, Calfee School memories, Clark's
   Chapel United Methodist Church, choir/gospel favorites (Richard Smallwood),
   nursing career, COVID-era church changes, aging/shrinking congregation.
2. **Randy & Natasha Grubb** — interviewed by Clay Adkins, ~19.5 min, at First
   Baptist Church (Magazine Street). Topics: growing up as a pastor's family,
   Pulaski County Schools then vs. now, scarcity of Black teachers, staying in
   Pulaski for family, church as chosen family, revitalization of Pulaski,
   gospel favorite (Kirk Franklin's "Smile").

Both transcripts are clean Word docs with speaker-turn structure (e.g. `C:` /
`P:`) and header metadata (narrator, interviewer, date, transcriber, keywords).
Audio was recorded as uncompressed WAV (~250MB / ~206MB); the user is
converting these to mp3 themselves before they're added to the site (avoids
GitHub's ~100MB per-file limit and is standard for web audio delivery anyway).

## Data structure (CB-OH format)

- **`_data/filters.csv`** — defines the theme taxonomy as `tag,description`
  rows. The colored bar's colors are auto-assigned by cycling through a fixed
  20-color palette in the order tags appear in this file (see
  `_includes/transcript/style/filter-style.html`) — no manual color config
  needed.
- **`_data/transcripts/<objectid>.csv`** — one file per interview, columns
  `speaker, words, tags, timestamp`. One row per speaker turn. `tags` is
  semicolon-separated when multiple themes apply to a turn. `timestamp` is
  `h:mm:ss`, set at the start of each turn.
- **Main metadata CSV** — one row per interview: title, interviewee,
  interviewer, date, location, description, keywords/subject,
  `display_template: transcript`, `object_location` (path to the mp3).

### Theme taxonomy (initial)

- Stories of Joy
- Stories of Faith
- Stories of Struggle
- Community & Family
- Education & Integration
- Gospel Music
- Activism & Change

Confirmed as a starting point; tags can be added, renamed, or split later by
editing `_data/filters.csv` and the affected transcript rows.

## Processing pipeline

1. **Audio**: user converts WAV → mp3 and drops files into
   `SOF-oral-histories-source/audio/`. mp3s get moved into the new repo's
   `objects/` directory.
2. **Timestamps via forced alignment**: run Whisper against each mp3 to get
   its own word-level timestamps, then sequence-match those words against the
   *existing, human-edited* transcript text. This preserves the transcript's
   exact wording/cleanup while attaching accurate timing — avoids discarding
   edits by re-transcribing from scratch, and avoids fully manual
   timestamping by ear.
3. **Segment into speaker turns**: both transcripts are already structured as
   speaker turns; each turn becomes one row in the interview's transcript CSV
   with its aligned start timestamp.
4. **Theme tagging (first pass by Claude, reviewed by user)**: tag each
   segment against the taxonomy above. Ambiguous calls are flagged as
   questions rather than guessed silently. User reviews/corrects before the
   tags are considered final.
5. **Assemble CB-OH data files**: populate `_data/filters.csv`, per-interview
   transcript CSVs, and the main metadata CSV rows; place mp3s in `objects/`.
6. **Verify locally**: run `bundle exec jekyll serve`, confirm both interview
   pages render with working audio playback, timestamp sync, and the
   color-coded thematic bar.

## Out of scope for this pass

- The other ~98 existing oral histories (this design covers the first 2 as a
  proof of concept; the same pipeline repeats for additional interviews).
- Publishing/GitHub Pages deployment (can follow once local verification
  passes).
- Video interviews (both current interviews are audio-only).
- Any changes to the existing `soulsonfire` repo.
