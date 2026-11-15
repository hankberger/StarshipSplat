"""Remove floaters around the tower and ship by checking every above-ground splat against the 142 source frames.

A splat is in "free space" from a frame's point of view if, at the pixel it projects to, that frame saw something
farther away: the ground, a structure surface well behind it, or open sky. Splats that most frames say are in free
space are floaters. Real structure is seen as structure from nearly every frame, so it survives.
"""
import os, sys, json
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2, numpy as np
import spz

SRC = sys.argv[1] if len(sys.argv) > 1 else '../rocket/splats_r2/cleaned_disc_soft.spz'
DST = sys.argv[2] if len(sys.argv) > 2 else '../rocket/splats_r2/cleaned_disc_carved.spz'
MARGIN = float(os.environ.get("CARVE_MARGIN", 0.9))          # scene units a splat must be in front of the seen surface to count as floating
MIN_VOTES, MAX_FREE = 4, float(os.environ.get("CARVE_FREE", 0.55))

def q2R(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

d = spz.read(SRC); P = spz.positions(d).astype(np.float32); S = spz.scales(d).max(1); alpha = d['alpha'][:, 0]
AX = np.array([0.56, 0.88]); r = np.linalg.norm(P[:, [0, 2]] - AX, axis=1)
air = (P[:, 1] > 2.2) & (r < 60)                      # candidates: everything standing above the ground
idx = np.where(air)[0]; Q = P[idx]
print('splats', len(P), 'above-ground candidates', len(idx))

proxy = np.load('proxy.npy')
frames = json.load(open('scene/operation.json'))['response']['frames']
votes = np.zeros(len(idx), np.int32); free = np.zeros(len(idx), np.int32)
KS = int(os.environ.get("CARVE_KERNEL", 7)); kernel = np.ones((KS, KS), np.uint8)
for fi, f in enumerate(frames):
    c = f['camera']; K = c['intrinsics']; R = q2R(c['extrinsics']['quaternion']).astype(np.float32); t = np.array(c['extrinsics']['position'], np.float32)
    D = cv2.imread(f'scene/clean/depth_{fi:03d}.exr', cv2.IMREAD_UNCHANGED); D = (D if D.ndim == 2 else D[..., 0]).astype(np.float32)
    # nearest known structure surface at each pixel, from the structure seen in the sharp frames
    pc = (proxy - t) @ R; z = -pc[:, 2]; m = z > 0.5
    u = np.round(K['cx'] + K['fx'] * pc[m, 0] / z[m]).astype(int); v = np.round(K['cy'] - K['fy'] * pc[m, 1] / z[m]).astype(int); zz = z[m]
    inb = (u >= 0) & (u < 1280) & (v >= 0) & (v < 720)
    zb = np.full(720 * 1280, np.inf, np.float32); np.minimum.at(zb, v[inb] * 1280 + u[inb], zz[inb]); zb = cv2.erode(zb.reshape(720, 1280), kernel)
    vv, uu = np.mgrid[0:720, 0:1280]
    diry = R[1, 0] * (uu - K['cx']) / K['fx'] + R[1, 1] * (-(vv - K['cy']) / K['fy']) - R[1, 2]
    # project the candidate splats
    qc = (Q - t) @ R; qz = -qc[:, 2]; ok = qz > 0.5
    qu = np.round(K['cx'] + K['fx'] * qc[:, 0] / np.where(ok, qz, 1)).astype(int); qv = np.round(K['cy'] - K['fy'] * qc[:, 1] / np.where(ok, qz, 1)).astype(int)
    ok &= (qu >= 4) & (qu < 1276) & (qv >= 4) & (qv < 716)
    k = np.where(ok)[0]; pu, pv, pz = qu[k], qv[k], qz[k]
    zs = zb[pv, pu]; dd = D[pv, pu]; sky = diry[pv, pu] > 0.012
    has_struct = np.isfinite(zs); has_ground = np.isfinite(dd) & ~has_struct
    is_free = np.where(has_struct, pz < zs - MARGIN, np.where(has_ground, pz < dd - MARGIN, sky))
    voted = has_struct | has_ground | sky
    votes[k] += voted; free[k] += (is_free & voted)
    if fi % 20 == 0: print('frame', fi, 'voted', int(voted.sum()), 'free', int((is_free & voted).sum()))

frac = free / np.maximum(votes, 1)
floater = (votes >= MIN_VOTES) & (frac > MAX_FREE)
# also drop big, see-through blobs hanging in the air near the structures
blob = (S[idx] > 1.2) & (alpha[idx] < 120)
remove = floater | blob
print('votes pct', np.percentile(votes, [5, 50, 95]), ' floaters', int(floater.sum()), ' blobs', int((blob & ~floater).sum()))
near_tower = r[idx] < 8
print('within 8 units of the tower: candidates', int(near_tower.sum()), 'removed', int((remove & near_tower).sum()))
second = np.linalg.norm(Q[:, [0, 2]] - np.array([8.0, -37.0]), axis=1) < 8
keep = np.ones(len(P), bool); keep[idx[remove]] = False
print('kept', spz.write(DST, d, keep), 'of', len(P))
np.save('carve_frac.npy', np.c_[idx, votes, frac])
