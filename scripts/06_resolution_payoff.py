"""F06 — Does raising capture resolution improve a CROPPED read?

HYPOTHESIS   moondream's input is ~378px; a crop from 1080p is ~269x573, i.e.
             being upscaled. Raising capture to 1440p should feed it natively.
METHOD       Same physical region cropped from frames captured at two
             resolutions. n=5 each (see F04 — n=1 would be noise).
MEASURED     Word-for-word identical descriptions. The prediction was WRONG.
WHY          The ceiling is the model's SEMANTIC resolution, not the frame's
             optical resolution. It reads "bookshelf with books" from gross
             structure and cannot read a spine at any resolution.
UNTESTED     TEXT. That is the one case where detail should convert to meaning.
USAGE        python 06_resolution_payoff.py <lowres.jpg> <highres.jpg>
"""
import sys, collections, cv2
from _common import describe, jpeg, emit, load

P = ("This is a close crop from a camera. Describe exactly what you see, "
     "concretely. If there is any readable text, say what it says.")
# fractional box so the same physical region is taken from either resolution
BOX = (0.22, 0.75, 0.28, 0.42)      # y0, y1, x0, x1
res = {}
for path in sys.argv[1:3]:
    im = load(path); h, w = im.shape[:2]
    c = im[int(BOX[0]*h):int(BOX[1]*h), int(BOX[2]*w):int(BOX[3]*w)]
    b = jpeg(c, 92)
    outs = [describe(b, P, 90)[0] for _ in range(5)]
    mode, cnt = collections.Counter(outs).most_common(1)[0]
    res[f"{w}x{h}"] = {"crop_px": f"{c.shape[1]}x{c.shape[0]}", "modal_share": cnt/5, "text": mode}
    print(f"=== source {w}x{h}, crop {c.shape[1]}x{c.shape[0]} ({cnt}/5 agree)\n    {mode[:190]}\n")
vals = list(res.values())
if len(vals) == 2:
    print("IDENTICAL OUTPUT — you are semantically bound, not optically bound."
          if vals[0]["text"] == vals[1]["text"] else "Outputs differ; check against F04 variance first.")
emit("F06", res)
