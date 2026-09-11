"""
CISAI logo reveal animation generator
======================================
Generates assets/images/about-history.gif — the animated reveal of the
CISAI icon showing awareness (grey outer loop + black dot), technological
progress (red), and the need for existential security (blue).

Path data below is extracted from
cisai_thumbnail_10_with_backing.svg (the "backing" rect is ignored — the
figure background stays transparent, matching every earlier version of
this animation).

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
# Grey path is a single <path> with two subpaths (separate "m" moves):
# the inner hook, then the outer loop. Both render together with the dot.
D_GREY = ("m 5413.9429,-197.81414 c 0,0 2.4503,-1.43097 2.4974,-6.84701 "
          "0.069,-7.91831 6.9251,-6.92513 6.9251,-6.92513 "
          "m -10e-5,0 c 0,0 -12.9846,-0.86565 -12.9846,7.79076 "
          "0,8.65641 12.9846,7.79077 12.9846,7.79077")
D_RED  = "m 5408.6495,-196.00475 c 0,0 7.7908,0.86564 7.7908,-8.6564 0,-7.79077 6.9251,-6.92513 6.9251,-6.92513"
D_BLUE = "m 5423.3653,-211.58628 v 15.58153"
DOT_CENTER = (5420.0977, -203.79553)
DOT_RADIUS  = 0.56659263
# Backing rect origin (x, y) from the SVG; offsetting by its negative moves
# the icon's own coordinate space to start at (0, 0).
OFFSET = (-5402.0576, 217.74757)

# ---------- Path parser (m/c/v relative commands only) ----------
def sample_cubic(p0, p1, p2, p3, n=60):
    ts = np.linspace(0, 1, n)
    mt = 1 - ts
    x = (mt**3)*p0[0] + 3*(mt**2)*ts*p1[0] + 3*mt*(ts**2)*p2[0] + (ts**3)*p3[0]
    y = (mt**3)*p0[1] + 3*(mt**2)*ts*p1[1] + 3*mt*(ts**2)*p2[1] + (ts**3)*p3[1]
    return list(zip(x, y))

def parse_path(d):
    """Parses m/c/v/M/C/V commands. Returns a list of subpaths (each a
    numpy array of points) — a new subpath starts at every 'm'/'M'."""
    tokens = re.findall(r'([MmCcVvLl])([^MmCcVvLl]*)', d)
    cur = (0.0, 0.0)
    subpaths = []
    poly = []
    for cmd, nums_str in tokens:
        nums = [float(n) for n in re.findall(r'-?\d*\.?\d+(?:e-?\d+)?', nums_str)]
        if cmd in ('m', 'M'):
            if poly:
                subpaths.append(np.array(poly))
                poly = []
            cur = (cur[0]+nums[0], cur[1]+nums[1]) if cmd == 'm' else (nums[0], nums[1])
            poly.append(cur)
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
    if poly:
        subpaths.append(np.array(poly))
    return subpaths

def apply_offset(poly):
    return poly + np.array(OFFSET)

poly_grey_subs = [apply_offset(sp) for sp in parse_path(D_GREY)]
poly_red      = apply_offset(parse_path(D_RED)[0])
poly_blue     = apply_offset(parse_path(D_BLUE)[0])
dot_center    = (DOT_CENTER[0]+OFFSET[0], DOT_CENTER[1]+OFFSET[1])

# Scale the mark up around its own bounding-box centre. Strokes scale with
# it (see LW_MAIN/LW_GREY/DOT_R below) so proportions stay identical to the
# source SVG, just bigger.
MARK_SCALE = 1.4
_all_pts = np.vstack(poly_grey_subs + [poly_red, poly_blue])
_mark_center = np.array([
    (_all_pts[:,0].min() + _all_pts[:,0].max()) / 2,
    (_all_pts[:,1].min() + _all_pts[:,1].max()) / 2,
])

def scale_about_center(poly, center, scale):
    return (poly - center) * scale + center

poly_grey_subs = [scale_about_center(sp, _mark_center, MARK_SCALE) for sp in poly_grey_subs]
poly_red       = scale_about_center(poly_red, _mark_center, MARK_SCALE)
poly_blue      = scale_about_center(poly_blue, _mark_center, MARK_SCALE)
poly_blue_rev  = poly_blue[::-1]
dot_center     = tuple(scale_about_center(np.array([dot_center]), _mark_center, MARK_SCALE)[0])

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
# The new icon (27.9mm viewBox) is smaller than the old one (46.9mm); scale
# every layout constant proportionally so the composition (padding, legend
# spacing, stroke widths) stays visually equivalent.
DATA_W = 27.899689
_SCALE = DATA_W / 46.865479
PAD = 5.0 * _SCALE
LEGEND_SPACE = 27.8 * _SCALE
XLIM = (-PAD, DATA_W+PAD)
YLIM = (-PAD, DATA_W+PAD+LEGEND_SPACE)
FIG_W = 8.0
FIG_H = FIG_W * ((YLIM[1]-YLIM[0]) / (XLIM[1]-XLIM[0]))
DPI = 100
PT_PER_DATA_UNIT = FIG_W * 72 / (XLIM[1]-XLIM[0])

# Grey outer loop/hook render together with the black dot (the "awareness"
# stage); red and blue grow in afterward, as before.
LEGEND_ITEMS = [
    ("#aba5ab", "AWARENESS"),
    ("#d40a12", "TECHNOLOGICAL PROGRESS"),
    ("#0e4fe8", "NEED FOR EXISTENTIAL SECURITY"),
]
LEGEND_FONT     = "JetBrains Mono"
LEGEND_FONTSIZE = 22.0 * _SCALE * 1.7   # text 70% bigger
LEGEND_SQ       = 4.8 * _SCALE
LEGEND_ROW_PITCH = LEGEND_SQ + 4.0 * _SCALE * 0.5   # gap between rows halved
LW_MAIN = 1.6229 * PT_PER_DATA_UNIT * MARK_SCALE
LW_GREY = 1.6    * PT_PER_DATA_UNIT * MARK_SCALE
DOT_R   = 1.6 * _SCALE * MARK_SCALE
GREY, RED, BLUE = "#aba5ab", "#d40a12", "#0e4fe8"
DOT_COLOR = "#000000"

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

def render_frame(grey_alpha, red_frac, blue_frac, overall_alpha=1.0, legend_alpha=None):
    if legend_alpha is None:
        legend_alpha = overall_alpha
    ax.clear()
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")

    oa = overall_alpha

    # Awareness stage: grey outer loop/hook and the black dot appear together.
    if grey_alpha > 0.001:
        for sp in poly_grey_subs:
            ax.plot(sp[:,0], sp[:,1], color=GREY, alpha=grey_alpha * oa,
                    linewidth=LW_GREY, solid_capstyle="round", zorder=1)
        ax.add_patch(plt.Circle(dot_center, DOT_R, color=DOT_COLOR, alpha=grey_alpha * oa, zorder=2))

    if red_frac > 0.001 and oa > 0.001:
        seg = reveal(poly_red, red_frac)
        ax.plot(seg[:,0], seg[:,1], color=RED, linewidth=LW_MAIN, solid_capstyle="round",
                alpha=oa, zorder=1)

    if blue_frac > 0.001 and oa > 0.001:
        seg = reveal(poly_blue_rev, blue_frac)
        ax.plot(seg[:,0], seg[:,1], color=BLUE, linewidth=LW_MAIN, solid_capstyle="round",
                alpha=oa, zorder=1)

    legend_y0 = DATA_W + 2.4 * _SCALE   # gap above the key trimmed slightly
    for i, (color, label) in enumerate(legend_layout):
        ly = legend_y0 + i * LEGEND_ROW_PITCH
        ax.add_patch(FancyBboxPatch(
            (SWATCH_X0, ly), LEGEND_SQ, LEGEND_SQ,
            boxstyle=f"round,pad=0,rounding_size={ROUNDING}",
            mutation_scale=1, linewidth=0, facecolor=color, alpha=legend_alpha, zorder=3))
        ax.text(TEXT_X, ly + LEGEND_SQ/2, label, va="center", ha="left",
                fontsize=LEGEND_FONTSIZE, family=LEGEND_FONT, color="#000000", alpha=legend_alpha, zorder=3)

    fig.canvas.draw()
    frames_rgba.append(np.asarray(fig.canvas.buffer_rgba()).copy())

# ---------- Timeline ----------
GREY_FRAMES = 36
GREY_HOLD   = 12
GROW_FRAMES  = 72
FINAL_HOLD   = 108
FADE_FRAMES  = 28

render_frame(0.0, 0.0, 0.0)
for i in range(GREY_FRAMES):
    render_frame(ease_in_out_cubic(i/(GREY_FRAMES-1)), 0.0, 0.0)
for _ in range(GREY_HOLD):
    render_frame(1.0, 0.0, 0.0)
for i in range(GROW_FRAMES):
    te = ease_in_out_cubic(i/(GROW_FRAMES-1))
    render_frame(1.0, te, te)
for _ in range(FINAL_HOLD):
    render_frame(1.0, 1.0, 1.0)
for i in range(FADE_FRAMES):
    t = (i + 1) / FADE_FRAMES
    render_frame(1.0, 1.0, 1.0, overall_alpha=1.0 - ease_in_out_cubic(t), legend_alpha=1.0)

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

# Use a fully-opaque peak frame (just before fade) as palette basis —
# NOT the last frame, which is fully transparent and has no colour info.
palette_frame_idx = -(FADE_FRAMES + 5)
first_c = pil_frames_cropped[palette_frame_idx].convert("P", palette=Image.ADAPTIVE, colors=64)
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
