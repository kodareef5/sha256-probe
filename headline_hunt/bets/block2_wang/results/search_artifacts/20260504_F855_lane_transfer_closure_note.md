# F855 Lane Transfer Closure Note

This note closes the next F846 transfer probes after F850.

## F845: bit25 HW84 -> bit13 HW82 lane mobility

F843 already tested bit25 -> bit13 with target weight 2 plus mild shape bias
and found no improvement. F845 repeated the transfer with a stronger lane
objective and no shape bias:

- source: bit25 HW84
- target lane: bit13 HW82 `[10, 11, 9, 12, 9, 7, 10, 14]`
- objective: `HW + 4 * lane_L1`
- pair pool: 1024
- beam width: 1024
- max pairs/radius: 6/12

Result:

- init objective: 124
- pair-pool objective range: 157..227
- best objective: 124, still the init
- best seen HW: 84, still the init
- no new records
- wall: 745.58s

Verdict: bit25->bit13 is closed as both a repair test and a pure lane-mobility
test at this beam scale.

## F851/F852: bit18 HW86 -> bit14 HW85

F851 pair-potential gate:

- initial target L1: 21
- HW-improving pairs: 0
- HW-nonworse pairs: 1
- c/g-improving pairs: 0
- target-L1-improving pairs: 31
- best target pair: L1 15 at HW98

F852 1M six-pair combo sample:

- evaluated combos: 999,970
- HW<86: 0
- HW<=86: 0
- c/g-improving: 0
- target-L1-improving: 283
- best HW combo: HW90, target L1 25
- best target combo: target L1 12, HW95
- wall: 166.59s

Verdict: target-shape density is nonzero, but it does not produce a repairable
near-HW detour in 1M combos.

## F853/F854: bit12 HW86 -> bit14 HW85

F853 pair-potential gate:

- initial target L1: 21
- HW-improving pairs: 0
- HW-nonworse pairs: 0
- c/g-improving pairs: 0
- target-L1-improving pairs: 36
- best target pair: L1 15 at HW96

F854 1M six-pair combo sample:

- evaluated combos: 999,963
- HW<86: 0
- HW<=86: 0
- c/g-improving: 2
- target-L1-improving: 274
- best HW combo: HW90, target L1 25
- best target combo: target L1 13, HW98
- wall: 151.36s

Verdict: similar to bit18->bit14, with no repairable near-HW detour.

## Combined Read

Simple portfolio transfer is failing at three levels:

- nearest-lane transfer: bit25->bit13 cannot move even under stronger lane
  weighting;
- M2-close transfer: bit14->bit25 and bit6->bit15 were false positives under
  pair-potential gates;
- target-density transfer: bit18/bit12 -> bit14 has nonzero target-shape
  density, but all detours are too expensive.

The next useful direction is not another full repair beam from these transfer
detours. It is an upstream selector that explicitly searches for F788-like
balanced repair coverability before promoting a detour.
