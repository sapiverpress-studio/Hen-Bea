# Hen & Bea Video Dataset and Lesson Production

## Long-term goal

Build a reusable library of short, consistent Hen & Bea music-lesson clips that supports:

1. a truth-labelled video training dataset; and
2. edited 15-minute lesson videos with narration, sound, titles and transitions.

A 15-minute lesson should not be generated as one continuous AI video. It should be assembled from short approved shots, voice-over, music examples, pauses, reusable room shots and simple editorial transitions.

## Generation stages

### Stage 1 — ten-scene pilot

Run `Hen & Bea Ten-Scene Pilot Batch` in GitHub Actions. Scenes run sequentially and each receives one paid Hailuo attempt.

### Stage 2 — review and truth labelling

For every clip, preserve:

- source still;
- generated MP4;
- generation prompts;
- raw JSON and console logs;
- observed caption describing the actual output;
- quality score;
- review status;
- issue tags.

The observed caption must describe what appears in the video, even when character roles or actions differ from the generation prompt.

Allowed review statuses:

- `accept`
- `accept_relabelled`
- `trim_then_accept`
- `reject`

### Stage 3 — scale to 50 clips

Scale only after the pilot establishes which actions and prompt structures remain stable. Add scenes in controlled batches rather than changing infrastructure between individual failures.

### Stage 4 — training-material package

The final training ZIP should contain only accepted or trimmed-and-accepted clips, plus their observed captions and manifest rows. Rejected clips remain in a separate audit folder and are not used for training.

### Stage 5 — 15-minute lesson assembly

Use approved clips as visual building blocks. A typical 15-minute lesson will require more than 50 timeline placements because some clips will be reused, held as still frames, slowed, looped carefully, or separated by narration and learner-response pauses.

## Acceptance rules

A clip is usable when:

- Hen and Bea remain identifiable;
- the action is readable;
- major anatomy remains coherent;
- props remain understandable;
- there is no destructive scene change;
- a truthful caption can describe the result.

Role reversal, simplified timing and small expression changes do not automatically require rejection. They require accurate relabelling.

Reject clips with severe identity loss, merged bodies, destructive extra limbs, unreadable action, major scene replacement or irrecoverable prop corruption.

## Current pilot

`prompts/pilot_batch_01.json` contains ten music-lesson actions. The batch runner writes `output/manifests/pilot_batch_01.json` and captures per-scene console logs even when an individual task fails.
