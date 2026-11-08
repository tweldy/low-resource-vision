"""F08 — Does your frame-corruption metric survive a resolution change?

HYPOTHESIS   Row-mean jitter detects partially-decoded MJPG frames.
METHOD       Capture at several resolutions, compute jitter at each.
MEASURED     1080p 0.47, 1440p 0.37, 2160p 0.25 — the metric DECREASES with
             resolution, because more rows means smaller adjacent differences.
             A threshold calibrated at 1080p is meaningless at 2160p, and the
             author nearly declared a known-corrupt mode clean because of it.
TAKEAWAY     Any statistic whose scale depends on input dimensions must be
             recalibrated per resolution. Keep a human-visible ground truth —
             the frames are written out here for exactly that reason.
NOTE         Capture under the SAME LOAD as production. A USB 2.0 camera that is
             clean with nothing else running can corrupt when a microphone on
             the same device is also streaming isochronously.
USAGE        python 08_resolution_sweep.py /dev/video0 [outdir]
"""
import sys, cv2, numpy as np
from _common import emit

dev = sys.argv[1] if len(sys.argv) > 1 else "/dev/video0"
out = sys.argv[2] if len(sys.argv) > 2 else "."
def jitter(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.abs(np.diff(g.mean(axis=1))).mean())
res = {}
for w, h in ((1920,1080),(2560,1440),(3840,2160)):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if not cap.isOpened(): continue
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    got = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    js, last = [], None
    for i in range(6):
        ok, img = cap.read()
        if ok and img is not None and i: js.append(jitter(img)); last = img
    cap.release()
    if not js: res[f"{w}x{h}"] = {"negotiated": got, "frames": 0}; continue
    cv2.imwrite(f"{out}/sweep_{w}x{h}.png", last)
    res[f"{w}x{h}"] = {"negotiated": f"{got[0]}x{got[1]}", "jitter_median": round(float(np.median(js)),2)}
    print(f"asked {w}x{h:<5} got {got[0]}x{got[1]:<5} jitter {np.median(js):6.2f}  -> sweep_{w}x{h}.png")
emit("F08", res)
print("\nLOOK AT THE SAVED FRAMES. The metric is not the ground truth.")
