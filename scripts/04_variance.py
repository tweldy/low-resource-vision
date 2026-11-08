"""F04 — How much does a VLM's output vary on IDENTICAL input?

HYPOTHESIS   One run per condition is enough to compare image pipelines.
METHOD       Same image, same prompt, N runs. Count distinct outputs.
MEASURED     1 run in 5 dropped a major object (a television) entirely.
WHY IT MATTERS  Run-to-run variance equals or exceeds most preprocessing
             effects. Any n=1 A/B comparison of VLM output is measuring noise.
             RUN THIS FIRST, before trusting any other comparison you make.
USAGE        python 04_variance.py <image.jpg> [n]
"""
import sys, collections
from _common import describe, jpeg, emit, load

im = load(sys.argv[1] if len(sys.argv) > 1 else "frame.jpg")
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
b = jpeg(im)
outs = [describe(b)[0] for _ in range(n)]
for i, o in enumerate(outs, 1):
    print(f"  {i}. {o[:150]}")
c = collections.Counter(outs)
emit("F04", {"n": n, "distinct_outputs": len(c), "modal_share": c.most_common(1)[0][1]/n,
             "outputs": outs})
print(f"\n{len(c)} distinct outputs in {n} runs. "
      f"If >1, do not compare pipelines at n=1.")
