# F859 Shape-Aware Transfer Ranking Note

F857 updates the portfolio transfer ranking with transition shape columns:
added bits, removed bits, and net M2 growth. This makes a failure mode visible
that plain lane/M2 distance hid.

## Shape Read

Top candidates by the original score:

- bit25 HW84 -> bit13 HW82: balanced shape, 26 add / 25 remove, but far
  distance 51. F843/F845 closed it under target beams.
- bit14 HW85 -> bit25 HW84: add-heavy, 27 add / 11 remove. F847/F848 closed
  it cheaply.
- bit6 HW85 -> bit15 HW83: balanced, 18 add / 18 remove, but F849 had zero
  target-improving one-pair moves.
- bit12 HW86 -> bit14 HW85: balanced, 10 add / 10 remove. F853/F854 found
  target density but no near-HW detour.
- bit18 HW86 -> bit14 HW85: mild add-heavy, 12 add / 8 remove. F851/F852
  found target density but no near-HW detour.

The ranking is now more diagnostic:

- balanced but far can still be immobile;
- near-M2 but add-heavy often means construction/growth, not repair transfer;
- balanced and near-M2 still needs local target density plus near-HW support.

## F858: bit2 HW86 -> bit25 HW84

F857 showed bit2 -> bit25 as a remaining balanced downhill candidate:

- HW: 86 -> 84
- lane L1: 20
- M2 xor distance: 54
- transition shape: 27 add / 27 remove

F858 pair-potential gate:

- initial target L1: 20
- HW-improving pairs: 0
- HW-nonworse pairs: 0
- c/g-improving pairs: 0
- target-L1-improving pairs: 16
- best HW pair: HW95
- best target pair: L1 15 at HW97

Verdict: balanced shape alone is not enough. Bit2->bit25 is closed at the
cheap pair-potential gate and should not be promoted to a combo or repair beam.

## Updated Rule

Before launching a full transfer beam, require all three:

1. plausible transition shape, preferably balanced or only mildly net-add;
2. nontrivial one-pair or combo target-density signal;
3. at least one near-HW state, not just an expensive target-shaped detour.

The current portfolio transfer set fails this rule.
