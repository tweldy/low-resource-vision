"""F07 — Does a VLM decode a stick figure?

HYPOTHESIS   One circle and five lines conveys "person" — any child reads it.
METHOD       Draw it, ask four different ways.
MEASURED     Neutral prompt -> "!!!STICKER!!!". "Is there a person in this
             picture?" -> EMPTY STRING. "How many people are drawn here?" ->
             EMPTY STRING. Told it is a line drawing, it says "a black and white
             stick figure standing upright ... on its hind legs". It reaches the
             GENRE LABEL and never arrives at "person".
WHY          A stick figure is a PROTOCOL, not a compression. Five strokes carry
             almost nothing; a human supplies the rest from an involuntary
             body-schema detector. Every compression scheme is a bet about the
             receiver, and this one bets on a visual cortex.
USAGE        python 07_stick_figure.py
"""
import numpy as np, cv2
from _common import describe, png, emit

K = (0, 0, 0)
a = np.full((480, 480, 3), 255, np.uint8)
cv2.circle(a, (240,110), 45, K, 6)
for p0, p1 in (((240,155),(240,300)), ((240,190),(150,270)), ((240,190),(330,270)),
               ((240,300),(170,420)), ((240,300),(310,420))):
    cv2.line(a, p0, p1, K, 6)
b = png(a)
res = {}
for q in ("What is in this picture? Answer in one short sentence.",
          "Is there a person in this picture? Answer yes or no.",
          "How many people are drawn here?",
          "This is a simple line drawing. What does it depict?"):
    txt, _ = describe(b, q, 60)
    res[q] = txt
    print(f"  Q: {q}\n  A: {txt!r}\n")
emit("F07", {"kb": round(len(b)/1024, 1), "answers": res})
print("If the yes/no and count questions returned empty strings, the model has "
      "no decoder for this protocol. That is the finding.")
