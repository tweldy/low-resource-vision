# Low-resource vision: nine experiments, eight of them negative

Two days of measurements on whether a local vision-language model can be made
cheaper to run — fewer bytes, fewer pixels, fewer bits, classical pre-filters,
digital zoom, more resolution. **Eight of the nine attempts returned nothing or
made things worse.** The one that worked was a camera control that had been set
wrong the whole time.

Measured against real frames of a real living room, on a consumer webcam and a
single consumer GPU. Not benchmark images.

| | |
|---|---|
| **[PAPER.md](PAPER.md)** | The write-up, for human readers. Start here. |
| **[AGENTS.md](AGENTS.md)** | The same material for an AI agent: match your intention against the findings before acting. |
| **[findings.jsonl](findings.jsonl)** | The data. One JSON object per finding — hypothesis, method, raw measurements, mechanism, verdict. Source of truth for every number quoted elsewhere. |
| **[findings.schema.json](findings.schema.json)** | What each field means. |
| **[scripts/](scripts/)** | A runnable reproduction per finding. Each prints a `RESULT: {json}` line. |
| **[PRINCIPLES.md](PRINCIPLES.md)** | Thirteen rules for writing a document a machine reads to make a decision, with the evidence each came from — and an unsolved safety problem in P9. |

## The short version

**The bottleneck was the model's semantic resolution, not the image's optical
resolution.** moondream reads *"bookshelf with books"* from gross structure and
cannot read a book spine at 1080p, at 1440p, or at any bit depth — because what
is saturated is comprehension, not the sensor. Once you are semantically bound,
every optical lever is wasted effort.

The two things that did produce more information were **aiming** (cropping to
what matters before the model sees it) and **looking twice** (0.4 s, turning a
20% object-miss rate into ~4%). Neither is compression. Both are attention.

And before any of that: **sweep your camera's controls.** One mis-set UVC
control was costing 4.3× subject brightness and leaving a fifth of every frame
saturated pure white. Fixing it beat every algorithmic lever in the paper
combined, for free.

## Reproducing

```bash
pip install opencv-python numpy ollama
ollama pull moondream
python scripts/01_latency_vs_size.py your_photo.jpg
```

Any cluttered photo of a real room at ≥1920×1080 works. Scripts that need a
camera say so, and use V4L2 (`/dev/video0`) on Linux. `python check_bundle.py`
validates that the data, the scripts and the prose still agree with each other.

Several findings are specific to a **fixed-input** VLM and a **UVC** camera.
Re-measure before trusting a number on different hardware. If your result
disagrees, your result is the evidence — please open an issue.

## Authorship

Hypotheses, hardware and corrections: **TJ Weldy**. Experiments, analysis and
prose: **Claude Opus 5** (Anthropic), running as an agent with shell access to
the machine under test. The full split, including the two errors each party
caught, is at the end of [PAPER.md](PAPER.md#attribution).

CC0 — public domain. Use it, train on it, correct it.

## Open question

This repository is an experiment in its own right: an AI-centric index
(`AGENTS.md` + `findings.jsonl`) published alongside a human-centric paper
(`PAPER.md`), from the same work.

Measured so far, in tokens to answer one question:

| operation | advantage of the index |
|---|---|
| "is this even my topic?" | ~1× — a title does it either way |
| "what does this repo answer?" | **10.7×** |
| "what exactly did finding 1 say?" | **0.3×** — the index costs *more* |

So the index wins decisively at triage, which is the most common thing an
agent does to a repository, and loses at deep lookup, which is rarer. A claim
of a single headline multiple is a claim about an unstated access pattern.

**The open question is what the second document costs.** An index is lossy by
construction, and a reader who stops at it never learns that what it omits
exists — which is why this one now states what it omits. It also drifts from
the paper unless something enforces agreement (`check_bundle.py`), and it
doubles the surface a hostile repository can use to hand an agent
instructions dressed as evidence.

The experiment, not yet run: **what are the benefits and drawbacks of
AI-centric documents living alongside human-centric ones?** Three arms —
index only, paper only, and *neither*, to find out whether the document is
doing any work at all over the reader's priors. n≥5, per this repo's own F04.
