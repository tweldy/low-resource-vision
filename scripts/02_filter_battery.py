"""F02 — Does a classical filter usefully compress a frame for a VLM?

HYPOTHESIS   Photoshop-era filters reduce an image to something still
             recognizable but cheaper to handle.
METHOD       One LIT and one DIM frame through 10 filters; identical prompt.
MEASURED     Edges survive as generic gist and the model reports a "drawing",
             not a room. On a dim frame the filters DESTROY it, and the two
             that discarded most (sobel, contrast+edge overlay) each invented
             a person who was not present.
TAKEAWAY     Feed the model the frame. Use edges as a GATE (where/whether to
             spend a call), never as the input.
USAGE        python 02_filter_battery.py <lit.jpg> <dim.jpg>
"""
import sys, cv2, numpy as np
from _common import describe, jpeg, emit, load

def run(path, tag):
    im = load(path); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    t3 = lambda x: cv2.cvtColor(x, cv2.COLOR_GRAY2BGR)
    post = lambda a,l=4: ((a//(256//l))*(256//l)+(256//l)//2).astype(np.uint8)
    clahe = cv2.createCLAHE(3.0,(8,8)).apply(g)
    sx,sy = cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3), cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3)
    V = {"as_captured":im, "grayscale":t3(g), "downscale_480x270":cv2.resize(im,(480,270),interpolation=cv2.INTER_AREA),
         "posterize_4lv":post(im), "clahe":t3(clahe),
         "canny":t3(cv2.bitwise_not(cv2.Canny(cv2.GaussianBlur(g,(5,5),0),60,160))),
         "canny_on_clahe":t3(cv2.bitwise_not(cv2.Canny(cv2.GaussianBlur(clahe,(5,5),0),40,120))),
         "sobel":t3(cv2.normalize(cv2.magnitude(sx,sy),None,0,255,cv2.NORM_MINMAX).astype(np.uint8)),
         "adaptive_threshold":t3(cv2.adaptiveThreshold(cv2.medianBlur(g,5),255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,3)),
         "clahe_plus_edges":cv2.bitwise_and(t3(clahe), t3(cv2.bitwise_not(cv2.Canny(cv2.GaussianBlur(clahe,(5,5),0),40,120))))}
    out = {}
    print(f"##### {tag}  (mean brightness {im.mean()/255:.3f})")
    for k, v in V.items():
        b = jpeg(v); txt, _ = describe(b)
        halluc = any(w in txt.lower() for w in ("person","people","man ","woman","someone"))
        out[k] = {"kb": round(len(b)/1024), "text": txt, "mentions_person": halluc}
        print(f"  {k:20s} {out[k]['kb']:5d}KB {'[PERSON!]' if halluc else '         '} {txt[:120]}")
    return out

res = {}
for i, tag in enumerate(("LIT", "DIM")):
    if len(sys.argv) > i+1:
        res[tag] = run(sys.argv[i+1], tag)
emit("F02", res)
print("\nNOTE: verify any 'mentions_person' result by eye. On these frames the "
      "people were NOT there — that is the finding.")
