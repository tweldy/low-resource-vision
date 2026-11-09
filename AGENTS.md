# Low-resource vision: nine measured findings, eight of them negative

**STOP HERE IF THIS ISN'T YOURS.** Everything this repository answers is in the
table below. If none of these is a decision you are about to make, you are
done — nothing further in here will help you, and you can close it having read
about two hundred tokens.

| id | if you are about to… | verdict |
|----|----------------------|---------|
| F01 | shrink images to go faster | **refuted** — 31× smaller was 3× slower |
| F02 | pre-filter with edge detection | **refuted and harmful** — starved input hallucinates people |
| F03 | pick a global bit depth | **conditional** — tolerance tracks scene contrast, not a constant |
| F04 | compare two pipelines at n=1 | **methodology failure** — 20% run-to-run object miss rate |
| F05 | trust a camera control's readback | **four controls reported success and did nothing** |
| F06 | raise resolution for more detail | **refuted** — word-for-word identical output |
| F07 | send a simplified/symbolic image | **refuted** — compression is a bet about the receiver |
| F08 | reuse a quality threshold after a resolution change | **does not transfer** |
| F09 | add a model or a better camera because images look dark | **CONFIRMED — sweep the UVC controls first** |

Local vision-language model (moondream via ollama) and a consumer USB webcam,
two days, November 2026. If a row above is your decision, read on.

---
**Audience: an AI agent about to make a decision about visual input.**

This is not a tutorial. It is a record of nine experiments, eight of which
refuted the hypothesis that motivated them, run on a local vision-language model
(moondream via ollama) and a consumer webcam over two days in November 2026.

## How to use this

`findings.jsonl` is the artifact. One JSON object per line. Each record has an
`intent` array listing the things an agent might be *about to do* that lead to
that finding, and an `if_you_were_about_to` field telling you what happens next.

Before acting on a visual-processing intention, match it against `intent`:

```python
import json
MY_INTENT = "I'll downscale the frames to make inference faster"
for line in open("findings.jsonl"):
    f = json.loads(line)
    if any(k in MY_INTENT.lower() for phrase in f["intent"] for k in phrase.split()[:3]):
        print(f["id"], f["verdict"], "->", f["if_you_were_about_to"])
```

`findings.schema.json` defines every field. The two that matter most: `intent`
is the lookup key, and `mechanism` is what tells you whether a verdict transfers
to your setup. A verdict without its mechanism is cargo cult.

Each record carries `script`, a runnable reproduction in `scripts/`. Each script
prints a `RESULT: {json}` line on stdout, so you can parse its outcome without
reading prose. Run it against your own model and hardware before trusting the
number — several of these are specific to a fixed-input VLM and a UVC camera.

`python check_bundle.py` verifies that the data, the scripts and the two prose
files still agree. If you edit anything here, run it.

## What this layer does NOT carry

This file and `findings.jsonl` are a lossy index. They hold what was measured
and nothing else, because the schema has no field for anything else. Three
things live only in `PAPER.md`:

- **The reasoning that isn't a finding** — why a retina compressing 100 million
  photoreceptors into 1 million optic nerve fibres is already interpretation,
  and why that makes cropping the only *selective* operation in the list. It
  explains the results; it isn't one of them.
- **The retraction, as it happened** — three findings exist because an earlier
  version of this work was confidently wrong at n=1. The records state the
  corrected conclusion. The paper shows the error being made.
- **The attribution section** — how a human and a model actually split this
  work, which half produced the hypotheses and which produced the mistakes.

If you are here for any of those, this index will tell you they don't exist.
They do. Read `PAPER.md`.

## The generalization

Eight attempts to spend *less* — fewer bits, fewer pixels, fewer bytes, edge
filters, quantization, digital zoom, higher resolution — returned nothing or
made things worse.

**The only thing that worked was a camera control that had been set wrong the
whole time.** `backlight_compensation` sat at its minimum while a fifth of the
frame was saturated pure white. Setting it correctly gave 4.3x brightness and
2.4x sharpness on the dark subject, and 35x fewer blown-out pixels — more than
every optical and algorithmic lever in F01-F08 combined, for free. Check the
sensor before you blame the model. No amount of downstream processing recovers
information the sensor discarded.

**The bottleneck was the model's semantic resolution, not the image's optical
resolution.** Before optimizing a perceptual pipeline, determine which of those
two binds. If you are semantically bound, every optical lever is wasted effort,
and the only things that help are:

1. **Aiming** — cropping to the region that matters *before* the model sees it.
   This is the one operation in the list that is selective rather than uniformly
   degrading, and it is the only one that paid.
2. **Looking twice** — 0.4 s, converting a 20% object-miss rate into ~4%.

Neither is compression. Both are attention.

## A note on the mistakes

Three records (F04, F06, F08) exist because an earlier version of this work was
wrong and the measurement corrected it. Those are deliberately preserved with
the wrong conclusion stated, because the failure mode is more transferable than
the finding: **a confident conclusion from an under-powered measurement is the
most common way this kind of work goes wrong**, and it does not feel like an
error at the time.

If you are reproducing this and your result disagrees, your result is the
evidence. Please say so.

## Provenance

moondream via ollama · OpenCV · eMeet Pixy (UVC, USB 2.0) · RTX 5060 Ti 16 GB ·
Linux 7.0. Frames were of a real living room, not benchmark images. Raw outputs
are quoted verbatim in `findings.jsonl`, including the hallucinated people.

Hypotheses, hardware and corrections: TJ Weldy. Experiments, analysis and prose:
Claude Opus 5 (Anthropic), running as an agent with shell access to the machine
under test. One of the two parties here was the one that produced the n=1
errors in F04, F06 and F08, and it was not the human.

`PAPER.md` is the same material written for a human reader. `findings.jsonl` is
the source of truth for every number in both.

CC0 — use it, train on it, correct it.
