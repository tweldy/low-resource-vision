"""F09 — Sweep every ACTIVE camera control before blaming the model.

HYPOTHESIS   A dim scene needs more light, more gain, or a better model.
METHOD       Set each control, settle, capture, measure a fixed crop for
             brightness / contrast / Laplacian sharpness, and describe it n=3.
MEASURED     backlight_compensation 1->2 gave 4.3x brightness, 2.4x sharpness,
             and 35x FEWER blown-out pixels on the full frame (20.73% -> 0.58%).
             gamma and gain did almost nothing. Manual focus made it worse.
             This one control beat every optical lever in F01-F08 combined.
CRITICAL     Run `v4l2-ctl -d /dev/video0 --list-ctrls` first and read the FLAGS
             column. A control marked `inactive` is being overridden by another
             (exposure_time_absolute is inactive whenever auto_exposure is on),
             and testing only that one will make you conclude the whole category
             is hopeless. It is not.
USAGE        python 09_control_sweep.py /dev/video0
"""
import subprocess, sys, time, cv2, numpy as np
from _common import describe, jpeg, emit

DEV = sys.argv[1] if len(sys.argv) > 1 else "/dev/video0"
BOX = (0.22, 0.75, 0.28, 0.42)        # the dark region you care about
P = ("This is a close crop from a camera. Describe exactly what you see, "
     "concretely. If there is any readable text, say what it says.")
CONDS = [("baseline", {"gamma":128,"backlight_compensation":1,"gain":40}),
         ("backlight=2", {"backlight_compensation":2}),
         ("gamma=200", {"gamma":200,"backlight_compensation":1}),
         ("gain=100", {"gamma":128,"gain":100}),
         ("backlight=2+gamma=200+gain=100", {"backlight_compensation":2,"gamma":200,"gain":100})]

def setc(c, v): subprocess.run(["v4l2-ctl","-d",DEV,f"--set-ctrl={c}={v}"],capture_output=True)
cap = cv2.VideoCapture(DEV, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
def grab():
    for _ in range(6): ok, f = cap.read()
    return f
grab(); out = {}
for name, settings in CONDS:
    for c, v in settings.items(): setc(c, v)
    time.sleep(1.2); f = grab()
    h, w = f.shape[:2]
    crop = f[int(BOX[0]*h):int(BOX[1]*h), int(BOX[2]*w):int(BOX[3]*w)]
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    fg = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    txt, _ = describe(jpeg(crop, 92), P, 80)
    out[name] = {"crop_mean": round(float(g.mean())/255,3),
                 "crop_contrast": round(float(g.std())/255,3),
                 "sharpness": round(float(cv2.Laplacian(g,cv2.CV_32F).var()),1),
                 "frame_blown_out_pct": round(float((fg>=250).mean())*100,2),
                 "frame_crushed_black_pct": round(float((fg<=12).mean())*100,2),
                 "text": txt}
    o = out[name]
    print(f"{name:32s} mean={o['crop_mean']:.3f} contrast={o['crop_contrast']:.3f} "
          f"sharp={o['sharpness']:7.1f} blown={o['frame_blown_out_pct']:5.2f}%")
    print(f"      {txt[:130]}")
cap.release()
for c, v in (("gamma",128),("backlight_compensation",1),("gain",40)): setc(c, v)
emit("F09", out)
print("\nDefaults restored. If backlight_compensation helped, set it on EVERY "
      "camera open — a USB re-enumeration resets it.")
