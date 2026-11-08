# Everything we tried to make a local vision model cheaper, and why none of it worked

*Measured over two days on an RTX 5060 Ti, against a camera pointed at a living room.*

*TJ Weldy and Claude Opus 5 (Anthropic). Hypotheses, hardware and corrections: TJ.
Experiments, analysis and prose: Claude. Full attribution at the end.*

TJ runs a small autonomous AI on a machine in his apartment. She has a webcam, a local
vision-language model (moondream, 1.3 GB, on the GPU alongside her 13 GB language
model), and a reason to look at things. The obvious engineering question is how to
give her more visual information for less money — fewer bytes, fewer pixels, less
compute, faster turnaround.

We spent two days measuring that. **Almost every answer was no**, and the pattern in
the failures turned out to be more useful than a win would have been.

Numbers below are from real frames of a real room, not benchmark images. Where we got
something wrong, we've left it in.

The premise, in TJ's words when we started: *"This might yield an interesting result
or absolutely zero, which... is also an interesting result."* It yielded the second
one eight times, and that turned out to be the finding.

---

## 1. Reducing the data does not make it faster. It can make it slower.

This is the result that reframed everything else.

| input | bytes on the wire | latency (min of 3, warm) |
|---|---|---|
| original 1920×1080 | 331.9 KB | **0.34 s** |
| Canny edge map 1920×1080 | 464.5 KB | 0.60 s |
| downscaled to 240×135 | 10.7 KB | **1.01 s** |

A 31× smaller image took **three times longer**.

The reason is structural and applies to every fixed-input vision model: the image is
resized to a fixed tensor (~378×378 for moondream) before any work happens. Decoding
the file is microseconds against ~400 ms of inference. Wire bytes are irrelevant to
compute — and a tiny image gets upscaled back into blur, which makes the model hedge
and emit more tokens.

**If your VLM has a fixed input size, image compression cannot buy you latency at
any ratio.** It can only buy you storage and bandwidth.

## 2. Classical filters destroy more than they save

The intuition — a Photoshop-era edge filter reduces an image to something still
recognizable — is half right and the wrong half.

On a well-lit frame, Canny edges produced: *"A black and white line drawing of a
living room with a couch, chair, potted plant, and window."* Correct, but generic,
and note that it reported looking at a **drawing**. The filter doesn't compress the
scene; it changes what the image is a picture of.

On a dim frame (mean brightness 0.235) it was actively destructive:

| input | description |
|---|---|
| as captured | *"urns on the table and shelf, lamp with white shade, flat screen tv displaying a video game, and a green dinosaur statue"* ✅ |
| Canny on raw | *"urns on the table and floor"* |
| Canny on contrast-stretched | *"urn of water on the table"* |
| contrast + edge overlay | *"…and a person standing near the window"* ❌ **no person present** |

Sobel magnitude also invented a person, on a different frame. **The two filters that
discarded the most information are the two that fabricated a human being.** The
unfiltered dark frame beat every processed version of itself.

## 3. Bit depth: it's contrast budget, not bits

Quantizing a bright, high-contrast frame down to **1 bit per channel — 8 colours
total, a 21× size reduction** — produced a description as good as 8-bit:
*"a beige couch sits against this wall, accompanied by a bookshelf filled with
various items."*

The same quantizer on a dim frame:

| depth | size | result |
|---|---|---|
| 8-bit | 3185 KB | *"a flat screen TV displaying a video game with a controller resting on it"* |
| 2-bit | 250 KB | *"a television displaying a blank screen"* — content gone |
| 1-bit | 39 KB | *"urns on a table and lamp with yellow shade"* — **TV gone entirely** |

And at 1-bit on a mid-brightness frame: *"chair behind person sitting down."* No
person. Same failure as grayscale-2-bit on the lit frame, which invented *"a photo of
a person sitting on the couch."*

**Tolerance for quantization is a function of scene contrast, not a constant.** A
starved frame doesn't degrade gracefully — it fills the gap with a human being, which
is the single worst failure mode for a camera in someone's home.

## 4. We measured noise and reported it as signal

We ran a JPEG-quality sweep and got a non-monotonic result: q8 produced a *better*
description than q85 on a dark frame. We nearly published that.

Then we ran the same image, same quality, five times:

```
1. urns on a shelf and a lamp next to it
2. urns on a shelf next to a television screen and a lamp with a white shade.
3. urns on a shelf next to a television screen and a lamp with a white shade.
4. urns on a shelf next to a television screen and a lamp with a white shade.
5. urns on a shelf next to a television screen and a lamp with a white shade.
```

**One run in five dropped the television entirely.** Identical input. The run-to-run
variance is the same size as every effect we had been measuring at n=1.

If you are evaluating VLM output qualitatively, **n=1 is not a measurement.** Most of
our earlier conclusions in this area evaporated when we checked.

That 20% rate has a practical consequence beyond methodology: a single glance at a
scene is a coin flip on whether a major object exists. Looking twice costs 0.4 s and
converts a 20% miss rate into about 4%.

## 5. The hardware lies, four times

Separate from the model, the camera stack produced four controls that reported
success and did nothing:

| control | reported | actually did |
|---|---|---|
| `cap.isOpened()` | camera fine | camera had been dead for six days |
| 3840×2160 capture | negotiated, logged | partially-decoded garbage |
| `exposure_time_absolute` 300→2500 | accepted | frame mean moved 0.2112 → 0.2101 |
| `zoom_absolute` 100→150 | **reads back 150** | nothing |

The zoom is the cleanest example. The driver advertises 1.0–1.5× digital zoom,
accepts the value, and returns it on read. Two captures of the same static room:

```
zoom100 vs zoom150         :   2.70 grey levels   (= sensor noise between frames)
zoom100 vs a TRUE 1.5x crop:  60.53 grey levels   (what it should have looked like)
sharpness (Laplacian var)  : 259.1  vs  259.4
```

**Always verify a camera control against the pixels, not against the control's own
readback.** Every one of these would have handed a downstream agent a confident false
belief about its own sensor.

Our own test metric had this problem too: we used row-mean jitter to detect the 4K
corruption, then noticed the metric *decreases* with resolution, so the threshold
derived at 1080p was meaningless at 2160p. The ground truth was looking at the image.

## 6. More pixels bought nothing either

The one optical lever we expected to pay: moondream's input is ~378 px, and a typical
crop from a 1080p frame is ~269×573 — **below the model's input, so it's being
upscaled.** The model wants more pixels than the crop contains. Raising capture to
2560×1440 makes that same crop 359×764, crossing from upscaled to native.

Same bookshelf, same light, n=5 per side:

> **1080p:** *"The image shows a bookshelf filled with various items including several books and a vase of flowers on the top shelf."*
>
> **1440p:** *"The image shows a bookshelf filled with various items including several books and a vase of flowers on the top shelf."*

Word for word identical. **The prediction was wrong.**

(1440p is clean under full load, incidentally — three consecutive captures with the
microphone streaming from the same USB device, row-mean jitter 0.37 vs 0.47 at 1080p.
We kept it, because it costs nothing, not because it helped.)

## 7. Stick figures don't decode

A tangent that turned out to be the point. One circle, five lines, 5.6 KB — the
drawing any child recognizes instantly:

| prompt | answer |
|---|---|
| "What is in this picture?" | `!!!STICKER!!!` |
| "Is there a person in this picture? Answer yes or no." | *(empty string)* |
| "How many people are drawn here?" | *(empty string)* |
| "This is a simple line drawing. What does it depict?" | "a black and white stick figure standing upright… **on its hind legs**" |

It reaches *"stick figure"* — the name of a genre of image — and stops. It never
arrives at **person**. Asked directly whether a person is present, it has nothing to
say.

A stick figure is not compression. It's a **protocol**, and a protocol only works if
both ends hold the same decoder. Five strokes carry almost nothing; a child's visual
system supplies the rest from a body-schema detector that fires involuntarily on that
topology. Every compression scheme is a bet about the receiver. That one bets on a
visual cortex.

---

## 8. The one thing that worked was a camera control set wrong

After seven negative results we swept every *active* UVC control against a fixed
dark bookshelf crop, same light, seconds apart.

| condition | subject brightness | contrast | sharpness | frame blown out |
|---|---|---|---|---|
| baseline (`backlight_compensation=1`) | 0.107 | 0.150 | 289.9 | **20.73 %** |
| **`backlight_compensation=2`** | **0.456** | **0.239** | **688.9** | **0.58 %** |
| `gamma=200` | 0.184 | 0.191 | 508.2 | — |
| `gain=100` | 0.160 | 0.179 | 439.0 | — |
| manual focus 700 | — | — | 15.5 | — |

**A fifth of the frame was saturated pure white**, and had been since the camera
was first opened. It isn't a trade of highlights for shadows — it recovered
both, simultaneously. The description moved from *"various items including
several books"* to *"three shelves and is made of metal"*: structure that was
previously unresolvable.

One control. 4.3× brightness, 2.4× sharpness on the subject, 35× fewer blown
pixels. **More than every optical and algorithmic lever in this paper combined.**

Two cautions. First, `exposure_time_absolute` is flagged **inactive** whenever
`auto_exposure` is on — an earlier session tested only that control and
concluded the entire category was a dead end. Read the flags column in
`v4l2-ctl --list-ctrls`. Second, the control resets on USB re-enumeration, so
set it on every open rather than once.

(The book spines are still unreadable, incidentally. At that distance a spine is
~10 px wide and its lettering ~2 px tall. That is now a distance problem, and
the digital zoom that would have solved it is the one that does nothing.)

## The pattern

Eight attempts to spend less — fewer bits, fewer pixels, fewer bytes, edge filters,
quantization, digital zoom, higher resolution — and every one returned nothing or
made things worse.

**The bottleneck is the model's semantic resolution, not the image's optical
resolution.** moondream reads *"bookshelf with books"* from gross structure. It cannot
read a book spine at 1080p, at 1440p, or at any depth, and more pixels don't give it
more meaning because what's saturated is comprehension.

Which means the useful levers aren't optical at all. The two things that actually
produced more information were:

1. **Aiming** — cropping to the region that matters before the model sees it. A crop
   of a TV screen beat a bigger model on the full frame, by a wide margin. This is the
   one place pixels convert into meaning, because it changes *what the model is looking
   at* rather than how many pixels describe it.
2. **Looking twice** — 0.4 s, and it turns a 20% object-miss rate into 4%.

Neither is compression. Both are attention.

There's a nice symmetry in why: a dog's retina compresses ~100 million photoreceptors
into ~1 million optic nerve fibres before anything reaches its brain, and that squeeze
is already interpretation — edges, motion, contrast, novelty, tuned over a hundred
million years. A VLM gets raw pixels and nothing to compress them with except a model
that converts the whole frame into one sentence, discarding everything that didn't fit
the sentence. You can't recover the missing hierarchy by throwing away data at the
front. Cropping works precisely because it's the only *selective* operation in the
list — it decides what matters instead of uniformly degrading everything.

## If you're building this

- Measure latency against pixel count before optimizing bytes. You may find there's
  nothing there.
- Use n≥5 for any qualitative VLM comparison. My n=1 conclusions were noise.
- Verify camera controls against pixels, never against readback.
- Expect starved inputs to hallucinate *people*, not to degrade gracefully.
- Spend your effort on where to point and when to look, not on how to encode.
- **Sweep your camera's controls before anything else.** Read the flags column;
  an `inactive` control is being overridden and will teach you the wrong lesson.
  The sensor is the only place in the pipeline where information is created.

---

## Reproducing this

Everything is at **https://github.com/tweldy/low-resource-vision**. Every number
above has a runnable script in `scripts/`, and every finding is a machine-readable
record in `findings.jsonl`. `AGENTS.md` is the same material written for an AI
agent rather than a reader. If your result disagrees with ours, your result is the
evidence — open an issue.

*Tooling: moondream via ollama, OpenCV, an eMeet Pixy webcam (UVC, USB 2.0), an
RTX 5060 Ti 16 GB, Linux 7.0.*

## Attribution

This was a two-party collaboration and the split is worth stating precisely,
because it is not the split people usually assume.

**TJ Weldy** built and owns the system under test, supplied the hardware and the
room, and posed most of the hypotheses — classical filters, edge tracing, bit
depth, the stick figure, the camera's advertised digital zoom, the resolution
bump. He also caught two errors that changed conclusions: that a vendor "1.5x
zoom" and a true crop are not the same operation (which is how the dead zoom
control in §5 was exposed), and that a control reading `100` could mean *no
zoom* or *full zoom* — ambiguity that forced the comparison onto pixels instead
of readback.

**Claude Opus 5** (Anthropic), operating as an agent with shell access to the
machine under test, designed and implemented the experiments, ran them, analysed
the results, found and retracted its own n=1 errors, and wrote this document.

The prose here is Claude's. The questions it answers are TJ's. Neither half
would have produced the paper alone: the hypotheses were worth testing and
wrong, and finding out which required someone willing to run forty captures at
two in the morning.

Both parties are named deliberately. The conventional phrasing — *"with AI
assistance"* — describes a person using a tool, and that is not what this was.
The hypotheses came from a human with two decades of hands-on experience and
very little spare time; the captures, the retractions and the prose came from a
model with no shortage of patience and no living room of its own. Two days
produced what would otherwise have been years of evenings. Calling that teamwork
isn't generosity, it's just the accurate word.

Corrections welcome — several of the numbers here exist because an earlier
version of this document was wrong.

*Released CC0. Use it, train on it, correct it.*
