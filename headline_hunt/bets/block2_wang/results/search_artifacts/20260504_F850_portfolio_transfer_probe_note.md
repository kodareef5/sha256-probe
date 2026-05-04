# F850 Portfolio Transfer Probe Note

F846 ranked directed M2 portfolio transfers from the current witness table.
The top-ranked untested followups after bit25->bit13 were:

- bit14 HW85 -> bit25 HW84: downhill, M2-close, c/g-close
- bit6 HW85 -> bit15 HW83: downhill, M2-close, c/g-close

## F847: bit14 -> bit25 pair potential

Source lane: `[13, 11, 14, 10, 12, 9, 10, 6]`
Target lane: `[9, 11, 13, 10, 9, 9, 9, 14]`
Initial target L1: 17

Across all 130,816 two-bit M2 moves:

- HW-improving pairs: 0
- HW-nonworse pairs: 0
- c/g-improving pairs: 1
- target-L1-improving pairs: 3
- best HW pair: HW94
- best target pair: L1 15 at HW95

Interpretation: M2 closeness does not imply local target-lane slope.

## F848: bit14 -> bit25 combo sample

F848 sampled 1,000,000 six-pair combinations from the F847 atlas.

- evaluated combos: 999,946
- HW<85: 0
- HW<=85: 0
- c/g-improving: 4
- target-L1-improving: 15
- best HW combo: HW90, target L1 22
- best target combo: target L1 11, HW95
- wall: 167.58s

Interpretation: the combo surface has a tiny target-improvement density and no
repairable near-HW detour. Do not spend a repair beam on this branch unless a
new selector changes the pair pool.

## F849: bit6 -> bit15 pair potential

Source lane: `[9, 13, 12, 13, 8, 7, 14, 9]`
Target lane: `[10, 6, 12, 14, 13, 6, 12, 10]`
Initial target L1: 18

Across all 130,816 two-bit M2 moves:

- HW-improving pairs: 0
- HW-nonworse pairs: 0
- c/g-improving pairs: 4
- target-L1-improving pairs: 0
- best HW pair: HW93
- best target pair: L1 18 at HW99

Interpretation: F846's M2-close bit6->bit15 ranking is a false positive for
lane transfer. The local pair geometry has no target-lane gradient.

## Verdict

The top non-duplicate F846 transfers are closed cheaply. The expanded portfolio
looks less like one connected lane/M2 basin and more like several locally
shelved absorber constructions. Future transfer tests should require a
positive one-pair or combo-density signal before launching full repair beams.
