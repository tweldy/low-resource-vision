"""F03 — How few bits does a VLM need?

HYPOTHESIS   There is a bit depth below 8 that is sufficient.
METHOD       Uniform quantization to 8/4/3/2/1 bits per channel, on a LIT frame
             and a DIM one.
MEASURED     A lit frame survives 1 bit/channel (8 colours, 21x smaller) with no
             loss of description. A dim frame loses the television at 2 bits and
             everything at 1, and a mid-brightness frame at 1 bit INVENTED a
             person.
TAKEAWAY     Tolerance tracks scene CONTRAST, not a constant. If you quantize,
             key the depth to a per-frame brightness/contrast statistic. And see
             F01: bit depth cannot buy latency, only storage.
USAGE        python 03_bit_depth.py <lit.jpg> <dim.jpg>
"""
import sys, numpy as np
from _common import describe, png, emit, load

def quant(a, bits):
    step = 256 / (2 ** bits)
    return (np.floor(a/step)*step + step/2).clip(0,255).astype(np.uint8)

res = {}
for i, tag in enumerate(("LIT", "DIM")):
    if len(sys.argv) <= i+1: continue
    im = load(sys.argv[i+1]); res[tag] = {}
    print(f"##### {tag} (mean {im.mean()/255:.3f})")
    for b in (8, 4, 3, 2, 1):
        img = im if b == 8 else quant(im, b)
        buf = png(img); txt, _ = describe(buf)
        halluc = any(w in txt.lower() for w in ("person","people","man ","woman"))
        res[tag][f"{b}bit"] = {"kb": round(len(buf)/1024), "text": txt, "mentions_person": halluc}
        print(f"  {b}-bit/ch {len(buf)/1024:6.0f}KB {'[PERSON!]' if halluc else '        '} {txt[:120]}")
emit("F03", res)
