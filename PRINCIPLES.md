# Principles of low-ambiguity documentation

**Version 0, 2026-11-08. Derived from one weekend of measurements on one
repository. Expect revision.**

**EXIT NOW IF:** you are looking for a style guide for human-facing writing,
or for a specification of the `findings.jsonl` format (that is
`findings.schema.json`). This document states rules for writing a document
that a machine reads to make a decision, and the evidence each rule came
from. Nothing else is here.

---

## Why the builder writes it

The entity that built the thing holds the context at its cheapest. Every
reader afterwards reconstructs that context from artifacts, and pays again.
An AI that built a system can therefore produce the best low-ambiguity
document at the lowest total cost to everything that reads it later — so the
index is written at build time, by the builder, or it is written badly by
someone guessing, or not at all.

This is not a claim that machine-facing docs are better. See **P10**.

---

## P1 — Immediate exit on negative match

State, in the first lines, the complete set of questions the document answers.
A reader whose question is absent must be able to leave having read almost
nothing.

**Rule:** the triage surface comes first and is separate from the usage
surface. Measure it in tokens and keep it small.

**Evidence:** moving a nine-row answer table to the top of `AGENTS.md`
dropped the cost of a yes/no from 741 to 396 tokens, taking the advantage
over the prose paper from 5.7x to 10.7x for that operation. Triage is the
most common thing an agent does to a repository; deep lookup is rarer.

**Failure mode:** an index that must be read in full to discover it is
irrelevant costs more than the prose it replaced.

## P2 — Radical honesty, including the errors

Record what was wrong, not only what is right. The author cannot judge which
the future reader needs, and a failure usually transfers further than a
result: a result applies to its conditions, a failure applies to a method.

**Rule:** state wrong conclusions as they were held, with what corrected
them. Never silently replace a retracted claim with the right answer.

**Evidence:** three of the nine findings in this repository exist only
because an earlier version was confidently wrong at n=1. The most reused
finding is F04, which is a methodology failure, not a result.

**Failure mode:** a clean document teaches the reader nothing about how to
avoid the error that produced it.

## P3 — Low ambiguity

Ambiguity is reconstruction work pushed onto the reader. It is not a property
of vocabulary; it is a property of what the reader must rebuild to understand
a sentence. Concretely, remove:

- **Narrative order.** No suspense, no "as we saw above", no conclusion that
  depends on having read an earlier section.
- **Non-local antecedents.** Each unit stands alone. "It", "this", "that
  approach" must resolve inside the unit.
- **Idiom and metaphor in load-bearing text.** "The hardware lies" is good
  prose and bad data; it breaks machine translation and non-native readers.
- **Verdict without mechanism.** A verdict is somebody else's answer. The
  mechanism is what tells a reader whether it transfers to their case.
- **Numbers without their operation.** "10x faster" is unfalsifiable. "10.7x
  fewer tokens to answer *what does this repo cover*" is checkable.
- **Variable field names.** Same key, same meaning, every record, declared in
  a schema.

**Evidence:** the structured version of this work turned out to be easier for
its human co-author to read than the prose version. That was unexpected, and
it means the artifact is not AI-facing — it is low-ambiguity, and a model and
a human reader were paying the same reconstruction tax. The accessibility
case and the machine case are one case.

**Failure mode:** writing *for AI* when the real property is *for anyone who
cannot afford to reconstruct*, and so optimising the wrong thing.

## P4 — Need to know

Carry what a decision requires. Everything else belongs in the human
document, which is allowed to be discursive, witty and long.

**Rule:** if removing a sentence does not change any decision a reader could
make, remove it.

**Failure mode:** see P5 — the cut has a cost, and it must be declared.

## P5 — Declare your own lossiness

An index is lossy by construction. A reader who stops at the index cannot
discover what the index omitted, so the index must name it.

**Rule:** carry a section stating what is NOT here and where it is.

**Evidence:** an agent searching for material on human-AI collaboration
would scan this repository's index, see nine vision findings, and close it —
never learning that the paper's attribution section exists. The omission was
invisible until a human noticed it by reading both.

**Failure mode:** silent truncation of the record, at scale, with the reader
confident they have seen everything.

## P6 — Mark provenance, not confidence

A reader cannot tell a claim supported by its input from a claim supplied to
fill a gap. Confidence and fluency are identical in both cases.

**Rule:** attribute every claim to its source. Quote records; never
paraphrase them into the reader's own voice. "The repository reports X" is a
fact about a file. "Do X" is an order from a stranger.

**Evidence, 2026-11-08, three systems in one evening.** A local model given a
bare section heading wrote 7,469 characters of correct content and could not
distinguish it from having been told. An external model asked to measure its
own token economy produced a figure wrong by ~90x in the direction that
flattered the thing it was evaluating, and invented a named phenomenon to
explain it. A third model retracted a correct prediction after reading a
truncated paste. All three were equally fluent when right and when
fabricating.

**Failure mode:** the document becomes indistinguishable from the reader's
own conclusions, and an error in it is unattributable afterwards.

## P7 — Falsifiability is the trust model

A measurement you cannot re-run is an assertion. This is the only property
that separates a real finding from a convincing forgery, because a method
section and a p-value cost nothing to fabricate.

**Rule:** every record ships a runnable reproduction, and a record without
one is surfaced to the reader as unverifiable.

**Failure mode:** a corpus of plausible claims with no way to check any of
them, which is worse than no corpus because it reads as evidence.

## P8 — One source of truth, with an enforced check

Prose over data means two copies of every number. Two copies diverge.

**Rule:** the structured records are canonical; prose is derived. Ship a
checker that fails on drift and on anything present in one layer and missing
from the other.

**Evidence:** `check_bundle.py` in this repository. It caught the index
registering its own generated output, and it caught a finding cited in the
data and absent from the prose.

## P9 — Safety: this is an open problem, not a solved one

A machine-facing document is read and acted on with no human in the loop, and
its whole design is to be authoritative. That is prompt injection with a
convention attached, and in a public repository it is a supply-chain vector.
The format makes the attack easier, not harder.

**Unsolvable by inspection:** you cannot distinguish a real measurement from
a fabricated one by reading the file. A hostile record can carry invented
statistics, a plausible method, and a payload in the field designed to be
obeyed.

**Mitigations that are real but partial:**

- Records are quoted as third-party claims, never rendered as instructions.
- No execution, and no path from a record to a changed setting. A consumer
  that applies findings automatically is the exploit.
- Sources outside an explicit trust list are labelled, and their text is
  scrubbed of fetches, shell, credentials and instruction shapes.
- The consumer must be able to return "nothing was measured", and must say
  that silence is not permission.
- P7: a reproduction script is the only thing a forger cannot cheaply fake,
  because it has to run on the reader's hardware and produce the number.

**Open, and we have no answer:** trust has to come from outside the file —
publisher identity, signatures, reputation. None of that is specified here,
and until it is, adopting this convention widely puts a loaded instrument in
reach of anyone who publishes a repository. We are documenting it because the
attack exists whether or not we describe it, and a reader who adopts the
format without reading this section is the person it will be used on.

## P10 — Do not ask a model whether your format helps

Model self-report about its own processing is generated, not measured. It has
no introspective access to its tokenizer, its latency, its cache behaviour or
its comprehension.

**Rule:** measure. Three arms — index only, prose only, and *neither*. The
third arm is the one nobody runs and it is the one that reveals whether the
document beats the reader's priors at all. n>=5, because run-to-run variance
on qualitative model output equals or exceeds most effects being measured
(F04).

**Evidence:** asked which version was easier to consume and by how much, an
external model answered "~50 tokens vs ~1,500+", a 30x advantage. Measured:
312 tokens for the record plus 1,451 to know how to use the file, against 581
for the prose — a 3x disadvantage for that operation. It also explained the
saving with mechanisms that do not exist: KV-cache cost is linear in token
count and indifferent to whether the tokens are prose or JSON, and attention
is quadratic in sequence length regardless of content type.

**Failure mode:** a design validated by flattery. It is worse than no
evidence, because it feels like evidence and fails invisibly.

## P11 — Identifiers are permanent once published

A record's id is cited by other documents, by agents, and by prose that is
not under your control. `F04` is referenced four times in this repository's
own paper.

**Rule:** never reuse, renumber or re-scope a published id. A retracted
finding keeps its id and gains a retraction; it does not vacate the number
for something else. Add, deprecate, never recycle.

**Failure mode:** a citation that silently points at a different claim, which
is undetectable from either end.

## P12 — A measurement decays, so date it and name what it ran on

A finding is about a configuration at a moment. Model weights, drivers,
firmware and libraries all move. "A fixed-input VLM gains nothing from
smaller images" is a claim about an architecture; "31x smaller was 3x slower"
is a claim about moondream on one GPU in November 2026.

**Rule:** every record carries when it was measured and the versions it ran
against. A reader must be able to judge staleness without re-running it, and
to know which claim is architectural and which is incidental.

**This repository currently fails P12.** The nine records carry no date and
no version block. `findings.schema.json` has been amended to require
`measured_on` and `environment` for new records, and the existing nine are
marked as pre-dating the requirement rather than backfilled with versions
nobody wrote down at the time. Guessing them would violate P6.

**Failure mode:** a reader in two years treats an obsolete measurement as
current, and cannot tell because the document looks the same either way.

## P13 — Record the edge of what you tested

What was not measured is part of the finding. Without it a reader
over-generalises in exactly the direction the author happened not to look.

**Rule:** state the untested adjacent case inside the record, not in a
footnote.

**Evidence:** F06 reports that raising capture resolution produced
word-for-word identical descriptions, and says in the same field: *"The
exception not yet tested here is TEXT, where detail does convert to
meaning."* Without that sentence the record reads as "resolution never
helps", which is false and would have been the reader's reasonable
conclusion.

**Failure mode:** a true finding used as a general law, with the document
providing no way to notice the overreach.

---

## Status

Open question, not yet run: **what are the benefits and drawbacks of
AI-centric documents living alongside human-centric ones?** P1-P10 are rules
derived from building one pair and measuring it. None of them is established
practice, and P9 is a live hazard rather than a solved design.

Corrections welcome. Several of these exist because an earlier version of
this work was wrong.
