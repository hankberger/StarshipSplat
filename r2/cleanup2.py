"""Second cleanup pass around the tower, ship and second tower. Run after carve.py; edits cleaned_disc_carved.spz in place."""
import numpy as np
import spz

PATH = '../rocket/splats_r2/cleaned_disc_carved.spz'
d = spz.read(PATH); P = spz.positions(d); Sc = spz.scales(d); S = Sc.max(1); smin = Sc.min(1); a = d['alpha'][:, 0]
rgb = ((d['color'].astype(np.float32) / 255 - 0.5) / 0.15 * 0.282 + 0.5) * 255
R, G, B = rgb[:, 0], rgb[:, 1], rgb[:, 2]; sat = rgb.max(1) - rgb.min(1); br = rgb.mean(1)
y = P[:, 1]
r_tower = np.linalg.norm(P[:, [0, 2]] - np.array([0.56, 0.88]), axis=1)
r_ship = np.linalg.norm(P[:, [0, 2]] - np.array([2.42, -0.14]), axis=1)
r_second = np.linalg.norm(P[:, [0, 2]] - np.array([3.19, -39.89]), axis=1)
air = y > 2.2
zone = (r_tower < 9) | (r_second < 9)

warm = (R >= G - 4) & (G >= B - 4)                               # rust, sand and steel tones run red >= green >= blue
tinted = zone & air & (sat > 38) & ~warm                         # green, blue, purple and magenta speckles
needle = zone & air & (S > 0.15) & (S / np.maximum(smin, 1e-4) > 12)   # long thin spikes
wisp = zone & air & (a < 90)                                     # faint see-through fuzz
plume = air & (r_second < 9) & (r_second > 2.3) & ((sat > 28) | (a < 140) | (S > 0.12))   # the smear beside the second tower
# The ship is dark, so pale splats hugging it are sky that bled onto its outline. The band where the tower's arms
# grip it is left alone: the arms are pale steel and would be stripped too.
ARMS = (13.9, 15.5)
fringe = (r_ship < 1.6) & (y > 10.2) & (y < 17.4) & (br > 105) & ~((y > ARMS[0]) & (y < ARMS[1]))

remove = tinted | needle | wisp | plume | fringe
for name, m in (('tinted speckles', tinted), ('spikes', needle), ('wisps', wisp), ('second-tower smear', plume), ('ship fringe', fringe)):
    print(f'{name}: {int(m.sum())}')
print('removed', int(remove.sum()), 'kept', spz.write(PATH, d, ~remove))

# A small clump of large splats hanging in the sky near the rim, on the opposite side of the base from the second tower.
# Nothing real stands that tall out there: away from both towers, anything more than 6 units above the ground goes.
d = spz.read(PATH); P = spz.positions(d)
stray = (P[:, 1] > 6) & (np.linalg.norm(P[:, [0, 2]] - np.array([0.56, 0.88]), axis=1) > 12) & (np.linalg.norm(P[:, [0, 2]] - np.array([3.19, -39.89]), axis=1) > 9)
print('stray sky clump:', int(stray.sum()), 'kept', spz.write(PATH, d, ~stray))

# Second tower. It sits near the rim, 40 units from the main tower, and was only ever seen small and from one side, so it
# came out as a rough column wrapped in haze. Keep a tight column around its fitted axis and its one arm platform; drop the rest.
d = spz.read(PATH); P = spz.positions(d); S = spz.scales(d).max(1); a = d['alpha'][:, 0]
rgb = ((d['color'].astype(np.float32) / 255 - 0.5) / 0.15 * 0.282 + 0.5) * 255; sat = rgb.max(1) - rgb.min(1)
y = P[:, 1]
ax_x, ax_z = 0.018 * y + 2.95, -0.010 * y - 39.63                 # the column's centre line, fitted from the splats (it leans very slightly)
ra = np.hypot(P[:, 0] - ax_x, P[:, 2] - ax_z)
zone = (np.hypot(P[:, 0] - 3.19, P[:, 2] + 39.89) < 10) & (y > 2.2)
clean = (sat < 30) & (a > 120) & (S < 0.22)                       # neutral, solid, reasonably small
column = (ra < 1.35) & (y < 17.8) & clean
platform = (ra < 3.6) & (y > 4.2) & (y < 6.8) & clean & (a > 150)
drop = zone & ~(column | platform)
print('second tower: zone', int(zone.sum()), 'kept', int((zone & ~drop).sum()), 'removed', int(drop.sum()), '| file kept', spz.write(PATH, d, ~drop))
