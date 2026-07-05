"""
Agent Ecosystem GIF generator
Composites per-agent PNGs into an animated GIF with transparent background.
"""

import os, re
import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
PNG_DIR    = os.path.join(REPO_ROOT, "assets", "images", "agent_ecosystem")
OUT_PATH   = os.path.join(REPO_ROOT, "assets", "images", "agent_ecosystem.gif")

BG_RGB         = (255, 255, 255) # matte colour agents fade in from
ALPHA_THRESH   = 0.01            # cumulative alpha below this → transparent pixel
FPS            = 18
FADE_FRAMES    = 30              # slower fade: ~1.7s per agent
STAGGER        = round(FADE_FRAMES * 0.4)   # next agent starts when prev is 40% done
HOLD_MS        = 8000
FADEOUT_FRAMES = 20
FRAME_MS       = round(1000 / FPS)

def ease(t):
    t = max(0.0, min(1.0, t))
    return 4*t**3 if t < 0.5 else 1 - (-2*t+2)**3/2

# ── Load PNGs sorted by numeric suffix ───────────────────────────────────────
files = sorted(
    [f for f in os.listdir(PNG_DIR) if f.endswith(".png") and re.search(r"\d+", f)],
    key=lambda f: int(re.search(r"(\d+)", f).group(1))
)
agents_rgba = [
    np.array(Image.open(os.path.join(PNG_DIR, f)).convert("RGBA"), dtype=np.float32)
    for f in files
]
N = len(agents_rgba)
H, W = agents_rgba[0].shape[:2]
print(f"Loaded {N} agents  {W}×{H}px  stagger={STAGGER} frames (60%)")
print("Order:", files)

agent_rgb = [a[:,:,:3] for a in agents_rgba]
agent_a   = [a[:,:,3:4] / 255.0 for a in agents_rgba]
BG        = np.array(BG_RGB, dtype=np.float32)

# ── Composite: Porter-Duff "over", returns RGBA (transparent where no agent) ─
def composite(ops) -> np.ndarray:
    # Accumulate agent colour and alpha independently (no BG baked in yet)
    c_col = np.zeros((H, W, 3), dtype=np.float32)
    c_a   = np.zeros((H, W, 1), dtype=np.float32)
    for i, op in enumerate(ops):
        if op <= 0.0:
            continue
        a_s   = agent_a[i] * op
        a_d   = c_a
        a_o   = a_s + a_d * (1.0 - a_s)
        denom = np.where(a_o > 0, a_o, 1.0)
        c_col = (agent_rgb[i] * a_s + c_col * a_d * (1.0 - a_s)) / denom
        c_a   = a_o

    # Blend agent composite with BG — gives smooth intermediate colours at low opacity
    final_rgb = c_col * c_a + BG * (1.0 - c_a)

    out = np.zeros((H, W, 4), dtype=np.uint8)
    visible = c_a[:,:,0] >= ALPHA_THRESH
    out[visible, :3] = np.clip(final_rgb[visible], 0, 255).astype(np.uint8)
    out[visible,  3] = 255
    return out

# ── Frame specs ───────────────────────────────────────────────────────────────
reveal_end  = (N - 1) * STAGGER + FADE_FRAMES
frame_specs = []
for frame in range(reveal_end):
    ops = [
        ease(max(0, frame - i*STAGGER) / (FADE_FRAMES - 1)) if frame >= i*STAGGER else 0.0
        for i in range(N)
    ]
    frame_specs.append((ops, FRAME_MS))
frame_specs.append(([1.0]*N, HOLD_MS))
for fo in range(FADEOUT_FRAMES):
    overall = 1.0 - ease((fo + 1) / FADEOUT_FRAMES)
    frame_specs.append(([overall]*N, FRAME_MS))

total_ms = reveal_end*FRAME_MS + HOLD_MS + FADEOUT_FRAMES*FRAME_MS
print(f"Frames: {len(frame_specs)}  Duration: {total_ms/1000:.1f}s")

# ── Composite all frames ──────────────────────────────────────────────────────
print("Compositing …")
frames_rgba, durations = [], []
for fi, (ops, dur) in enumerate(frame_specs):
    frames_rgba.append(composite(ops))
    durations.append(dur)
    if (fi+1) % 40 == 0 or fi == len(frame_specs)-1:
        print(f"  {fi+1}/{len(frame_specs)}")

# ── Convert to palette + transparency (magenta chroma-key) ───────────────────
MAGENTA = (255, 0, 255)

def to_palette_frame(rgba: np.ndarray, palette_img: Image.Image):
    img  = Image.fromarray(rgba, "RGBA")
    mask = img.split()[3]   # alpha channel
    # Composite onto magenta where transparent
    comp = Image.composite(
        img.convert("RGB"),
        Image.new("RGB", img.size, MAGENTA),
        mask
    )
    return comp.quantize(palette=palette_img, dither=1)

# Build palette from peak frame (all agents at full opacity) + magenta
print("Building palette …")
peak_rgba   = frames_rgba[reveal_end - 1]
peak_img    = Image.fromarray(peak_rgba, "RGBA")
peak_comp   = Image.composite(
    peak_img.convert("RGB"),
    Image.new("RGB", peak_img.size, MAGENTA),
    peak_img.split()[3]
)
palette_img = peak_comp.convert("P", palette=Image.ADAPTIVE, colors=255)

# Find the palette index closest to magenta
pal = palette_img.getpalette()
best_idx, best_dist = 0, None
for idx in range(len(pal) // 3):
    r, g, b = pal[idx*3], pal[idx*3+1], pal[idx*3+2]
    dist = (r-255)**2 + g**2 + (b-255)**2
    if best_dist is None or dist < best_dist:
        best_dist, best_idx = dist, idx
TRANS_IDX = best_idx
print(f"Transparency index: {TRANS_IDX}")

print("Quantising …")
p_frames = [to_palette_frame(f, palette_img) for f in frames_rgba]

# ── Save GIF ──────────────────────────────────────────────────────────────────
print("Saving …")
p_frames[0].save(
    OUT_PATH,
    save_all=True,
    append_images=p_frames[1:],
    duration=durations,
    loop=0,
    disposal=2,
    transparency=TRANS_IDX,
    optimize=False,
)

gif = Image.open(OUT_PATH)
n = 0
try:
    while True: n += 1; gif.seek(n)
except EOFError: pass

kb = os.path.getsize(OUT_PATH) // 1024
print(f"\nSaved {OUT_PATH}  ({n} frames · {W}×{H}px · {kb} KB)")
