"""
CISAI logo reveal animation generator
======================================
Generates assets/images/about-history.gif — the animated reveal of the
CISAI icon showing awareness (black), technological progress (red), and
the need for existential security (blue).

Requirements:
    pip install numpy scipy matplotlib pillow

Usage:
    python scripts/generate_about_gif.py

The output is written to assets/images/about-history.gif relative to
the repo root (run from the repo root, or adjust OUT_PATH below).

Note: the legend uses JetBrains Mono; if that font is not installed
matplotlib will fall back to a system sans-serif.
"""

import re
import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image

OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "images", "about-history.gif"
)

# ---------- Raw path data extracted from the SVG ----------
D_OUTER_LOOP = "m 1968.6169,-66.018575 c 0,0 -25.9405,-1.729379 -25.9405,15.564319 0,17.293689 25.9405,15.564331 25.9405,15.564331"
D_INNER_HOOK = "m 1950.0935,-38.562664 c 0,0 4.531,-3.40596 4.6886,-13.611663 0.2404,-15.562476 13.8348,-13.834962 13.8348,-13.834962"
D_RED  = "m 1939.2176,-34.880639 c 0,0 15.5645,1.729358 15.5645,-17.293688 0,-15.564331 13.8348,-13.834962 13.8348,-13.834962"
D_BLUE = "m 1968.6169,-66.018574 v 31.128649"
DOT_CENTER = (1962.0886, -50.454258)
DOT_RADIUS  = 1.1319337
OFFSET = (-1930.4847, 73.891439)

# ---------- Path parser (m/c/v relative commands only) ----------
def sample_cubic(p0, p1, p2, p3, n=60):
    ts = np.linspace(0, 1, n)
    mt = 1 - ts
    x = (mt**3)*p0[0] + 3*(mt**2)*ts*p1[0] + 3*mt*(ts**2)*p2[0] + (ts**3)*p3[0]
    y = (mt**3)*p0[1] + 3*(mt**2)*ts*p1[1] + 3*mt*(ts**2)*p2[1] + (ts**3)*p3[1]
    return list(zip(x, y))

def parse_path(d):
    tokens = re.findall(r'([MmCcVvLl])([^MmCcVvLl]*)', d)
    cur = (0.0, 0.0)
    poly = []
    for cmd, nums_str in tokens:
        nums = [float(n) for n in re.findall(r'-?\d*\.?\d+(?:e-?\d+)?', nums_str)]
        if cmd == 'm':
            cur = (cur[0]+nums[0], cur[1]+nums[1]); poly.append(cur)
        elif cmd == 'M':
            cur = (nums[0], nums[1]); poly.append(cur)
        elif cmd == 'v':
            for v in nums: cur = (cur[0], cur[1]+v); poly.append(cur)
        elif cmd == 'V':
            for v in nums: cur = (cur[0], v); poly.append(cur)
        elif cmd in ('c', 'C'):
            for i in range(0, len(nums), 6):
                c1x,c1y,c2x,c2y,ex,ey = nums[i:i+6]
                if cmd == 'c':
                    p1=(cur[0]+c1x,cur[1]+c1y); p2=(cur[0]+c2x,cur[1]+c2y); p3=(cur[0]+ex,cur[1]+ey)
                else:
                    p1,p2,p3=(c1x,c1y),(c2x,c2y),(ex,ey)
                seg = sample_cubic(cur, p1, p2, p3, n=60)
                poly.extend(seg[1:]); cur = p3
    return np.array(poly)

def apply_offset(poly):
    return poly + np.array(OFFSET)

poly_outer   = apply_offset(parse_path(D_OUTER_LOOP))
poly_inner   = apply_offset(parse_path(D_INNER_HOOK))
poly_red     = apply_offset(parse_path(D_RED))
poly_blue    = apply_offset(parse_path(D_BLUE))
poly_blue_rev = poly_blue[::-1]
dot_center   = (DOT_CENTER[0]+OFFSET[0], DOT_CENTER[1]+OFFSET[1])

# ---------- Arc-length reveal ----------
def reveal(poly, frac):
    if frac <= 0: return poly[:1]
    if frac >= 1: return poly
    seg_len = np.hypot(np.diff(poly[:,0]), np.diff(poly[:,1]))
    cum = np.concatenate([[0], np.cumsum(seg_len)])
    target = frac * cum[-1]
    idx = np.searchsorted(cum, target)
    if idx == 0: return poly[:1]
    t0, t1 = cum[idx-1], cum[idx]
    local_t = 0 if t1==t0 else (target-t0)/(t1-t0)
    interp = poly[idx-1] + (poly[idx]-poly[idx-1]) * local_t
    return np.vstack([poly[:idx], interp])

def ease_in_out_cubic(t):
    t = min(max(t, 0.0), 1.0)
    return 4*t*t*t if t < 0.5 else 1 - (-2*t+2)**3 / 2

# ---------- Layout ----------
DATA_W = 46.865479
PAD = 5.0
LEGEND_SPACE = 32.2  # reduced by ~1.78 data units (≈25px) to tighten the gap
XLIM = (-PAD, DATA_W+PAD)
YLIM = (-PAD, DATA_W+PAD+LEGEND_SPACE)
FIG_W = 8.0
FIG_H = FIG_W * ((YLIM[1]-YLIM[0]) / (XLIM[1]-XLIM[0]))
DPI = 100
PT_PER_DATA_UNIT = FIG_W * 72 / (XLIM[1]-XLIM[0])

LEGEND_ITEMS = [
    ("#000000", "AWARENESS"),
    ("#e2231a", "TECHNOLOGICAL PROGRESS"),
    ("#1c23e0", "NEED FOR EXISTENTIAL SECURITY"),
]
LEGEND_FONT     = "JetBrains Mono"
LEGEND_FONTSIZE = 22.0
LEGEND_SQ       = 4.8
LEGEND_ROW_PITCH = LEGEND_SQ + 4.0
LW_MAIN = 3.24222 * PT_PER_DATA_UNIT
LW_HOOK = 3.0     * PT_PER_DATA_UNIT
DOT_R   = 1.6
BLACK, RED, BLUE = "#000000", "#e2231a", "#1c23e0"

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
fig.patch.set_alpha(0.0); ax.patch.set_alpha(0.0)
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
inv = ax.transData.inverted()

GAP = 2.0
row_widths = []
legend_layout = []
for color, label in LEGEND_ITEMS:
    t = ax.text(0.0, 0.0, label, fontsize=LEGEND_FONTSIZE, family=LEGEND_FONT)
    fig.canvas.draw()
    bbox = t.get_window_extent(renderer=renderer)
    x0d = inv.transform((bbox.x0, bbox.y0))[0]
    x1d = inv.transform((bbox.x1, bbox.y1))[0]
    t.remove()
    row_widths.append(LEGEND_SQ + GAP + (x1d - x0d))
    legend_layout.append((color, label))

max_rw = max(row_widths)
SWATCH_X0 = XLIM[0] + ((XLIM[1]-XLIM[0]) - max_rw) / 2.0
TEXT_X    = SWATCH_X0 + LEGEND_SQ + GAP
ROUNDING  = LEGEND_SQ * 0.18

frames_rgba = []

def render_frame(black_alpha, red_frac, blue_frac):
    ax.clear()
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")

    if black_alpha > 0.001:
        ax.plot(poly_outer[:,0], poly_outer[:,1], color=BLACK, alpha=black_alpha,
                linewidth=LW_MAIN, solid_capstyle="round", zorder=1)
        ax.plot(poly_inner[:,0], poly_inner[:,1], color=BLACK, alpha=black_alpha,
                linewidth=LW_HOOK, solid_capstyle="round", zorder=1)
        ax.add_patch(plt.Circle(dot_center, DOT_R, color=BLACK, alpha=black_alpha, zorder=2))

    if red_frac > 0.001:
        seg = reveal(poly_red, red_frac)
        ax.plot(seg[:,0], seg[:,1], color=RED, linewidth=LW_MAIN, solid_capstyle="round", zorder=1)

    if blue_frac > 0.001:
        seg = reveal(poly_blue_rev, blue_frac)
        ax.plot(seg[:,0], seg[:,1], color=BLUE, linewidth=LW_MAIN, solid_capstyle="round", zorder=1)

    legend_y0 = DATA_W + PAD + 2.2  # reduced gap by ~1.78 data units (≈25px)
    for i, (color, label) in enumerate(legend_layout):
        ly = legend_y0 + i * LEGEND_ROW_PITCH
        ax.add_patch(FancyBboxPatch(
            (SWATCH_X0, ly), LEGEND_SQ, LEGEND_SQ,
            boxstyle=f"round,pad=0,rounding_size={ROUNDING}",
            mutation_scale=1, linewidth=0, facecolor=color, zorder=3))
        ax.text(TEXT_X, ly + LEGEND_SQ/2, label, va="center", ha="left",
                fontsize=LEGEND_FONTSIZE, family=LEGEND_FONT, color="#000000", zorder=3)

    fig.canvas.draw()
    frames_rgba.append(np.asarray(fig.canvas.buffer_rgba()).copy())

# ---------- Timeline ----------
BLACK_FRAMES = 36
BLACK_HOLD   = 12
GROW_FRAMES  = 72
FINAL_HOLD   = 52

render_frame(0.0, 0.0, 0.0)
for i in range(BLACK_FRAMES):
    render_frame(ease_in_out_cubic(i/(BLACK_FRAMES-1)), 0.0, 0.0)
for _ in range(BLACK_HOLD):
    render_frame(1.0, 0.0, 0.0)
for i in range(GROW_FRAMES):
    te = ease_in_out_cubic(i/(GROW_FRAMES-1))
    render_frame(1.0, te, te)
for _ in range(FINAL_HOLD):
    render_frame(1.0, 1.0, 1.0)

plt.close(fig)

# ---------- GIF export with transparency ----------
BG_KEY = (255, 0, 255)
pil_frames = []
for arr in frames_rgba:
    img = Image.fromarray(arr, "RGBA")
    mask = img.split()[3].convert("1", dither=Image.FLOYDSTEINBERG).convert("L")
    composed = Image.composite(img.convert("RGB"), Image.new("RGB", img.size, BG_KEY), mask)
    pil_frames.append(composed)

first = pil_frames[-1].convert("P", palette=Image.ADAPTIVE, colors=64)
quantized = [f.quantize(palette=first, dither=Image.NONE) for f in pil_frames]

pal = quantized[0].getpalette()
best_idx, best_dist = 0, None
for idx in range(len(pal)//3):
    r,g,b = pal[idx*3], pal[idx*3+1], pal[idx*3+2]
    dist = (r-BG_KEY[0])**2 + (g-BG_KEY[1])**2 + (b-BG_KEY[2])**2
    if best_dist is None or dist < best_dist:
        best_dist, best_idx = dist, idx

# ---------- Tight rectangular crop using original RGBA data ----------
# frames_rgba still has real alpha; pil_frames are already RGB+BG_KEY.
orig_h, orig_w = frames_rgba[0].shape[:2]
minx, miny = orig_w, orig_h
maxx, maxy = 0, 0
for arr in frames_rgba:
    mask = arr[:,:,3] > 10  # truly non-transparent pixels
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if rows.any():
        rmin, rmax = int(np.where(rows)[0][[0,-1]][0]), int(np.where(rows)[0][[0,-1]][1])
        cmin, cmax = int(np.where(cols)[0][[0,-1]][0]), int(np.where(cols)[0][[0,-1]][1])
        miny = min(miny, rmin); maxy = max(maxy, rmax)
        minx = min(minx, cmin); maxx = max(maxx, cmax)

crop_box = (minx, miny, maxx+1, maxy+1)
print(f"Cropping to {crop_box} (was {orig_w}x{orig_h})")
pil_frames_cropped = [f.crop(crop_box) for f in pil_frames]

first_c = pil_frames_cropped[-1].convert("P", palette=Image.ADAPTIVE, colors=64)
quantized_c = [f.quantize(palette=first_c, dither=Image.NONE) for f in pil_frames_cropped]

pal_c = quantized_c[0].getpalette()
best_idx_c, best_dist_c = 0, None
for idx in range(len(pal_c)//3):
    r,g,b = pal_c[idx*3], pal_c[idx*3+1], pal_c[idx*3+2]
    dist = (r-BG_KEY[0])**2 + (g-BG_KEY[1])**2 + (b-BG_KEY[2])**2
    if best_dist_c is None or dist < best_dist_c:
        best_dist_c, best_idx_c = dist, idx

quantized_c[0].save(
    OUT_PATH,
    save_all=True,
    append_images=quantized_c[1:],
    duration=[56]*len(quantized_c),
    loop=0,
    disposal=2,
    transparency=best_idx_c,
    optimize=False,
)
print(f"Saved {OUT_PATH}  ({len(quantized_c)} frames, size={pil_frames_cropped[0].size})")
