import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- Shared parameters ----------
N_LEVELS = 6
RADIUS_STEP = 1.38
BRANCH_CHOICES = [1, 2, 3]
BRANCH_PROBS = [0.2, 0.55, 0.25]
DIRICHLET_ALPHA = 1.2
SCALE_X = 1.55
SCALE_Y = 0.60
MIN_NODE_DIST = 0.567
RADIUS_JITTER_LOW = 0.65
RADIUS_JITTER_HIGH = 1.35
ANGLE_JITTER_FRAC = 0.12

def build_tree(seed, offset):
    rng = np.random.default_rng(seed)
    nodes = {}
    node_id = 0
    root_id = node_id
    nodes[root_id] = dict(level=0, pos=offset, parent=None,
                           angle_range=(0.0, 360.0), radius=0.0)
    node_id += 1
    level_nodes = {0: [root_id]}
    placed_positions = [np.array(offset)]

    def far_enough(candidate):
        pts = np.array(placed_positions)
        d = np.hypot(pts[:, 0] - candidate[0], pts[:, 1] - candidate[1])
        return np.min(d) >= MIN_NODE_DIST

    for level in range(1, N_LEVELS + 1):
        level_nodes[level] = []
        for parent_id in level_nodes[level - 1]:
            a0, a1 = nodes[parent_id]["angle_range"]
            span = a1 - a0
            parent_r = nodes[parent_id]["radius"]
            k = int(rng.choice(BRANCH_CHOICES, p=BRANCH_PROBS))
            weights = rng.dirichlet([DIRICHLET_ALPHA] * k)
            cursor = a0
            for j in range(k):
                width = weights[j] * span
                ca0, ca1 = cursor, cursor + width
                cursor = ca1
                cmid = (ca0 + ca1) / 2.0
                jitter = rng.uniform(-ANGLE_JITTER_FRAC, ANGLE_JITTER_FRAC) * max(width, 1.0)
                cmid += jitter
                rad = math.radians(cmid)
                step_len = RADIUS_STEP * rng.uniform(RADIUS_JITTER_LOW, RADIUS_JITTER_HIGH)
                r = parent_r + step_len
                x = offset[0] + r * math.cos(rad) * SCALE_X
                y = offset[1] + r * math.sin(rad) * SCALE_Y
                candidate = (x, y)
                if not far_enough(candidate):
                    continue
                nodes[node_id] = dict(level=level, pos=candidate, parent=parent_id,
                                       angle_range=(ca0, ca1), radius=r)
                level_nodes[level].append(node_id)
                placed_positions.append(np.array(candidate))
                node_id += 1

    edges_by_level = {
        level: [(nodes[nid]["parent"], nid) for nid in level_nodes[level]]
        for level in range(1, N_LEVELS + 1)
    }

    edge_timing = {}
    for level in range(1, N_LEVELS + 1):
        for (pid, cid) in edges_by_level[level]:
            start = rng.uniform(0.0, 0.5)
            duration = rng.uniform(0.45, 1.15)
            edge_timing[cid] = (start, duration)

    return dict(nodes=nodes, level_nodes=level_nodes,
                edges_by_level=edges_by_level, edge_timing=edge_timing)

SEED_A, OFFSET_A, COLOR_A = 0, (-0.35, 0.20), "#309530"   # green
SEED_B, OFFSET_B, COLOR_B = 17, (0.35, -0.20), "#1f6fd6"  # blue

tree_a = build_tree(SEED_A, OFFSET_A)
tree_b = build_tree(SEED_B, OFFSET_B)
trees = [(tree_a, COLOR_A), (tree_b, COLOR_B)]

# ---------- Easing ----------
def ease_in_out_cubic(t):
    t = min(max(t, 0.0), 1.0)
    if t < 0.5:
        return 4 * t * t * t
    p = -2 * t + 2
    return 1 - (p ** 3) / 2

def local_progress(edge_timing, global_t, cid):
    start, duration = edge_timing[cid]
    raw = (global_t - start) / duration
    raw = min(max(raw, 0.0), 1.0)
    return ease_in_out_cubic(raw)

# ---------- Bounds from combined node extents ----------
all_x, all_y = [], []
for tree, _ in trees:
    for nid in tree["nodes"]:
        x, y = tree["nodes"][nid]["pos"]
        all_x.append(x)
        all_y.append(y)
MAX_R_X = max(abs(min(all_x)), abs(max(all_x))) + 0.8
MAX_R_Y = max(abs(min(all_y)), abs(max(all_y))) + 0.8

DPI = 100
FIG_W = 10.0
FIG_H = FIG_W * (MAX_R_Y / MAX_R_X)
LINEWIDTH = 4.5
NODE_RADIUS_BASE = 0.13

FRAMES_PER_PHASE = 26
HOLD_FRAMES_BETWEEN = 4
FINAL_HOLD_FRAMES = 22

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
fig.patch.set_alpha(0.0)
ax.patch.set_alpha(0.0)
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

frames_rgba = []

def render_frame(completed_levels, growing_level, global_t, fade_alpha=1.0):
    ax.clear()
    ax.set_xlim(-MAX_R_X, MAX_R_X)
    ax.set_ylim(-MAX_R_Y, MAX_R_Y)
    ax.set_aspect("equal")
    ax.axis("off")

    for tree, color in trees:
        nodes = tree["nodes"]
        level_nodes = tree["level_nodes"]
        edges_by_level = tree["edges_by_level"]
        edge_timing = tree["edge_timing"]

        for lvl in range(1, completed_levels + 1):
            if lvl not in edges_by_level:
                continue
            for (pid, cid) in edges_by_level[lvl]:
                p0 = nodes[pid]["pos"]
                p1 = nodes[cid]["pos"]
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                         color=color, linewidth=LINEWIDTH, alpha=fade_alpha,
                         solid_capstyle="round", zorder=1)
        for lvl in range(0, min(completed_levels, N_LEVELS) + 1):
            for nid in level_nodes.get(lvl, []):
                x, y = nodes[nid]["pos"]
                node_alpha = 1.0 if lvl == 0 else fade_alpha  # root stays put through the fade
                circ = plt.Circle((x, y), NODE_RADIUS_BASE, color=color, alpha=node_alpha, zorder=2)
                ax.add_patch(circ)

        if growing_level is not None and growing_level in edges_by_level:
            for (pid, cid) in edges_by_level[growing_level]:
                p0 = np.array(nodes[pid]["pos"])
                p1 = np.array(nodes[cid]["pos"])
                te = local_progress(edge_timing, global_t, cid)
                tip = p0 + (p1 - p0) * te
                ax.plot([p0[0], tip[0]], [p0[1], tip[1]],
                         color=color, linewidth=LINEWIDTH, alpha=fade_alpha,
                         solid_capstyle="round", zorder=1)
                r = NODE_RADIUS_BASE * te
                if r > 0.001:
                    circ = plt.Circle((tip[0], tip[1]), r, color=color, alpha=fade_alpha, zorder=2)
                    ax.add_patch(circ)

    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    frames_rgba.append(buf.copy())

FRAME_DURATION_MS = 56
PAUSE_FRAMES = round(2500 / FRAME_DURATION_MS)   # ~2.5s pause on the fully-grown network
FADE_FRAMES = round(1700 / FRAME_DURATION_MS)    # ~1.7s fade to transparent

render_frame(completed_levels=0, growing_level=None, global_t=0.0)

for level in range(1, N_LEVELS + 1):
    for i in range(FRAMES_PER_PHASE):
        t = i / (FRAMES_PER_PHASE - 1)
        render_frame(completed_levels=level - 1, growing_level=level, global_t=t)
    for _ in range(HOLD_FRAMES_BETWEEN):
        render_frame(completed_levels=level, growing_level=None, global_t=1.0)

for _ in range(FINAL_HOLD_FRAMES):
    render_frame(completed_levels=N_LEVELS, growing_level=None, global_t=1.0)

for _ in range(PAUSE_FRAMES):
    render_frame(completed_levels=N_LEVELS, growing_level=None, global_t=1.0, fade_alpha=1.0)

for i in range(FADE_FRAMES):
    t = i / (FADE_FRAMES - 1)
    fade_alpha = 1.0 - ease_in_out_cubic(t)
    render_frame(completed_levels=N_LEVELS, growing_level=None, global_t=1.0, fade_alpha=fade_alpha)

plt.close(fig)

# ---------- Convert to GIF with real transparency ----------
BG_KEY = (255, 0, 255)

pil_frames = []
for arr in frames_rgba:
    img = Image.fromarray(arr, "RGBA")
    alpha = img.split()[3]
    # Floyd-Steinberg dithering approximates partial opacity as a dot pattern,
    # since GIF only supports binary (on/off) transparency, not real alpha blending.
    mask = alpha.convert("1", dither=Image.FLOYDSTEINBERG).convert("L")
    bg = Image.new("RGB", img.size, BG_KEY)
    rgb = img.convert("RGB")
    composed = Image.composite(rgb, bg, mask)
    pil_frames.append(composed)

# Base the shared palette on a fully-grown, fully-opaque frame (not frame 0 or a
# faded frame) so it reliably contains both tree colors plus the background key.
# Building it from a blank/near-blank frame produces a degenerate palette that
# can't represent the real colors, causing later frames to quantize to nothing.
palette_basis_index = FRAMES_PER_PHASE * N_LEVELS + HOLD_FRAMES_BETWEEN * N_LEVELS
palette_basis = pil_frames[min(palette_basis_index, len(pil_frames) - 1)]
first = palette_basis.convert("P", palette=Image.ADAPTIVE, colors=32)

quantized_frames = []
for frame in pil_frames:
    qf = frame.quantize(palette=first, dither=Image.NONE)
    quantized_frames.append(qf)

pal = quantized_frames[0].getpalette()
n_colors = len(pal) // 3
best_idx, best_dist = 0, None
for idx in range(n_colors):
    r, g, b = pal[idx*3], pal[idx*3+1], pal[idx*3+2]
    dist = (r-BG_KEY[0])**2 + (g-BG_KEY[1])**2 + (b-BG_KEY[2])**2
    if best_dist is None or dist < best_dist:
        best_dist, best_idx = dist, idx

durations = [FRAME_DURATION_MS] * len(quantized_frames)

out_path = os.path.join(REPO_ROOT, "assets", "images", "network_growth.gif")
quantized_frames[0].save(
    out_path,
    save_all=True,
    append_images=quantized_frames[1:],
    duration=durations,
    loop=0,
    disposal=2,
    transparency=best_idx,
    optimize=False,
)

print("Saved", out_path, "frames:", len(quantized_frames))
print("Tree A node counts:", {lvl: len(v) for lvl, v in tree_a["level_nodes"].items()})
print("Tree B node counts:", {lvl: len(v) for lvl, v in tree_b["level_nodes"].items()})
