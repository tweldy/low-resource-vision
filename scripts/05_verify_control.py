"""F05 — Did that camera control actually do anything?

HYPOTHESIS   A control that accepts a value and reads it back has applied it.
METHOD       Capture, set the control, capture again, compare PIXELS. Also
             compare against a simulation of the intended effect, so you can
             tell "no change" from "a change I failed to predict".
MEASURED     zoom_absolute 100->150 on an eMeet Pixy: reads back 150, pixel
             difference 2.70 grey levels (= sensor noise), while a true 1.5x
             crop differs by 60.53. The firmware ignores it.
ALSO SEEN    isOpened() True on a 6-day-dead camera; 3840x2160 negotiating
             cleanly and returning garbage; exposure_time_absolute silently
             INACTIVE because auto_exposure overrode it (check the flags field
             in `v4l2-ctl --list-ctrls`).
USAGE        python 05_verify_control.py /dev/video0 zoom_absolute 100 150
"""
import subprocess, sys, cv2, numpy as np
from _common import emit

dev, ctrl, lo, hi = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
def setc(v): subprocess.run(["v4l2-ctl","-d",dev,f"--set-ctrl={ctrl}={v}"],capture_output=True)
def getc():  return subprocess.run(["v4l2-ctl","-d",dev,f"--get-ctrl={ctrl}"],capture_output=True,text=True).stdout.strip()
def grab():
    cap=cv2.VideoCapture(dev,cv2.CAP_V4L2); cap.read()
    for _ in range(3): ok,f=cap.read()
    cap.release(); return f

setc(lo); a = grab()
setc(hi); readback = getc(); b = grab()
setc(lo)
ga,gb = (cv2.cvtColor(x,cv2.COLOR_BGR2GRAY).astype(np.float32) for x in (a,b))
diff = float(np.abs(ga-gb).mean())
h,w = ga.shape; r=float(hi)/float(lo) if float(lo) else 1.5
ch,cw = int(h/r),int(w/r); y0,x0=(h-ch)//2,(w-cw)//2
sim = cv2.resize(ga[y0:y0+ch,x0:x0+cw],(w,h))
simdiff = float(np.abs(ga-sim).mean())
res = {"control":ctrl,"readback":readback,"pixel_diff":round(diff,2),
       "pixel_diff_if_it_had_worked":round(simdiff,2),
       "verdict":"NO EFFECT — the control is a lie" if diff < simdiff/5 else "effect detected"}
print(f"readback: {readback}\npixel diff {diff:.2f} vs expected ~{simdiff:.2f}\n{res['verdict']}")
emit("F05", res)
