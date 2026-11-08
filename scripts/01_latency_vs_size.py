"""F01 — Does sending fewer bytes make a VLM faster?

HYPOTHESIS   A smaller image reduces inference time.
METHOD       One frame at three sizes, min of 3 warm runs each.
EXPECTED IF  the hypothesis holds: latency falls with bytes.
MEASURED     it rose. 31x smaller was 3x SLOWER.
WHY          A fixed-input VLM resizes everything to a fixed tensor (~378x378)
             before any work. Decode is microseconds against ~400ms inference.
             A tiny image is upscaled into blur and the model emits more tokens.
USAGE        python 01_latency_vs_size.py <image.jpg>
"""
import sys, cv2, numpy as np
from _common import describe, jpeg, emit, load

im = load(sys.argv[1] if len(sys.argv) > 1 else "frame.jpg")
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
canny = cv2.cvtColor(cv2.bitwise_not(cv2.Canny(cv2.GaussianBlur(g,(5,5),0),60,160)), cv2.COLOR_GRAY2BGR)
V = {"original": im, "canny": canny, "downscaled_240x135": cv2.resize(im,(240,135),interpolation=cv2.INTER_AREA)}
enc = {k: jpeg(v) for k, v in V.items()}
describe(enc["original"], n_predict=4)                      # warm the model
out = {}
for k, b in enc.items():
    ts = [describe(b)[1] for _ in range(3)]
    out[k] = {"kb": round(len(b)/1024, 1), "seconds_min": round(min(ts), 2)}
    print(f"{k:22s} {out[k]['kb']:7.1f} KB  {out[k]['seconds_min']:.2f}s")
emit("F01", out)
