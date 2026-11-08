"""Shared helpers. Every script here emits a RESULT: line of JSON on stdout so
an agent can parse the outcome without reading prose."""
import base64, json, sys, time
import cv2, numpy as np

MODEL = "moondream"
PROMPT = ("This is a live photo from your own camera, looking at the room you are in. "
          "Describe what you actually see in one or two sentences — objects, people, "
          "what is happening. Be concrete. Do not invent anything that is not visible.")

def describe(img_bytes, prompt=PROMPT, n_predict=110, model=MODEL):
    import ollama
    t0 = time.time()
    r = ollama.chat(model=model, messages=[{"role": "user", "content": prompt,
        "images": [base64.b64encode(img_bytes).decode()]}],
        options={"num_predict": n_predict})
    return (r["message"]["content"] or "").strip(), time.time() - t0

def jpeg(img, q=85):
    return cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), q])[1].tobytes()

def png(img):
    return cv2.imencode(".png", img)[1].tobytes()

def emit(finding_id, data):
    print("\nRESULT: " + json.dumps({"finding": finding_id, "measurement": data}))

def load(path):
    im = cv2.imread(path)
    if im is None:
        sys.exit(f"PRECONDITION FAILED: cannot read {path}. "
                 "Supply any photo of a cluttered real room, >=1920x1080.")
    return im
